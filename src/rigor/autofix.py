"""Auto-Fix Loop: Autonomous self-healing background worker for Rigor Kanban.

Combines:
1. Kanban task polling for `auto-fix` tagged tasks
2. Error parsing & deterministic patch generation
3. Lint/fix execution
4. Test execution & validation
5. Task status updates with retry limits
"""

from __future__ import annotations

import ast
import asyncio
import difflib
import json
import logging
import shutil
import sqlite3
import subprocess
import sys
import time
from contextlib import closing
from pathlib import Path
from typing import Any

from rigor.core.file_ops import FileOps
from rigor.core.patch_gen import ErrorParser, PatchGenerator

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("rigor.autofix")

SNAPSHOT_EXTENSIONS = {
    ".cfg",
    ".css",
    ".go",
    ".html",
    ".ini",
    ".java",
    ".js",
    ".json",
    ".md",
    ".py",
    ".rs",
    ".sh",
    ".toml",
    ".ts",
    ".txt",
    ".yaml",
    ".yml",
}
SNAPSHOT_EXCLUDES = {".git", ".venv", "__pycache__", "build", "dist", "htmlcov", "node_modules"}
DEFAULT_KANBAN_DB = "~/.hermes/kanban.db"
LEGACY_KANBAN_DB = "~/.hermes/kanban/board.db"


class ProjectDetector:
    @staticmethod
    def detect(workspace: Path | str) -> str:
        workspace = Path(workspace)
        if (
            (workspace / "pyproject.toml").exists()
            or (workspace / "requirements.txt").exists()
            or (workspace / "setup.py").exists()
        ):
            return "python"
        if (workspace / "package.json").exists():
            return "node"
        if (workspace / "go.mod").exists():
            return "go"
        if (workspace / "Cargo.toml").exists():
            return "rust"
        return "unknown"


class AutoFixEngine:
    def __init__(self, workspace: Path | str = "."):
        self.workspace = Path(workspace).resolve()
        self.project_type = ProjectDetector.detect(self.workspace)
        self.file_ops = FileOps(str(self.workspace))
        self.patch_gen = PatchGenerator(self.file_ops)

    def run_lint_fix(self) -> dict:
        cmds: list[list[str]] = []
        if self.project_type == "python":
            ruff_cmd = _python_module_cmd("ruff") or _binary_cmd("ruff")
            if ruff_cmd:
                cmds = [ruff_cmd + ["check", "--fix", "."], ruff_cmd + ["format", "."]]
        elif self.project_type == "node":
            cmds = [
                ["npx", "eslint", ".", "--fix", "--quiet"],
                ["npx", "prettier", ".", "--write", "--log-level", "warn"],
            ]
        elif self.project_type == "go":
            cmds = [["go", "fmt", "./..."], ["golangci-lint", "run", "--fix"]]

        logs: list[str] = []
        success = True
        for cmd in cmds:
            try:
                res = subprocess.run(cmd, cwd=self.workspace, capture_output=True, text=True, timeout=30)
                logs.append(f"$ {' '.join(cmd)}\n{res.stdout}\n{res.stderr}")
                if res.returncode != 0:
                    success = False
            except FileNotFoundError:
                logs.append(f"[WARN] {cmd[0]} not found. Skipping.")
            except Exception as e:
                logs.append(f"[ERROR] {cmd[0]} failed: {e}")
                success = False

        if not cmds:
            logs.append(f"No lint fixer configured or installed for project type: {self.project_type}.")

        return {"success": success, "logs": "\n".join(logs), "actions_taken": ["lint_fix"] if cmds else []}

    def run_tests(self) -> dict:
        cmds: list[str] = []
        if self.project_type == "python":
            if (self.workspace / "pytest.ini").exists() or (self.workspace / "pyproject.toml").exists():
                pytest_cmd = _python_module_cmd("pytest") or _binary_cmd("pytest")
                if pytest_cmd:
                    cmds = pytest_cmd + ["--tb=short", "-q", "--last-failed"]
        elif self.project_type == "node":
            cmds = ["npm", "test"]
        elif self.project_type == "go":
            cmds = ["go", "test", "./..."]

        if not cmds:
            return {"success": True, "logs": "No test runner detected.", "actions_taken": []}

        try:
            res = subprocess.run(cmds, cwd=self.workspace, capture_output=True, text=True, timeout=120)
            return {
                "success": res.returncode == 0,
                "logs": f"$ {' '.join(cmds)}\n{res.stdout}\n{res.stderr}",
                "actions_taken": ["test_run"],
            }
        except Exception as e:
            return {"success": False, "logs": f"Test runner failed: {e}", "actions_taken": []}

    def attempt_patch(self, error_output: str) -> dict:
        """Parse errors and generate/apply patches."""
        issues = ErrorParser.parse(error_output)
        if not issues:
            return {"success": False, "logs": "No specific issues found to patch.", "actions_taken": []}

        logs = []
        actions = []
        diffs = []
        for issue in issues:
            logger.info(f"  📝 Fixing {issue['file']}:{issue['line']} - {issue['message']}")
            patch = self.patch_gen.generate_patch(issue["file"], issue["line"], issue["message"])
            if patch:
                try:
                    if patch.startswith("import ") or patch.startswith("from "):
                        path = self.file_ops._safe_path(issue["file"])
                        current_content = path.read_text(encoding="utf-8", errors="replace")
                        new_content, changed = _insert_import(current_content, patch)
                        if changed:
                            path.write_text(new_content, encoding="utf-8")
                            logs.append(f"✅ Applied import: {patch}")
                            diffs.append(_unified_diff(issue["file"], current_content, new_content))
                            actions.append("patch_import")
                        else:
                            logs.append(f"ℹ️ Import already present: {patch}")
                    else:
                        logs.append(f"💡 Suggestion: {patch}")
                        actions.append("suggestion")
                except Exception as e:
                    logs.append(f"❌ Patch failed: {e}")

        return {"success": len(actions) > 0, "logs": "\n".join(logs), "actions_taken": actions, "diffs": diffs}


class AutoFixWorker:
    def __init__(
        self, db_path: str, workspace: str, poll_interval: int = 15, max_retries: int = 3, dry_run: bool = False
    ):
        self.db_path = db_path
        self.workspace = Path(workspace).resolve()
        self.poll_interval = poll_interval
        self.max_retries = max_retries
        self.dry_run = dry_run
        self.engine = AutoFixEngine(self.workspace)
        self.running = False

    def _get_db(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _fetch_pending_tasks(self) -> list[dict]:
        if not Path(self.db_path).exists():
            return []
        conn = self._get_db()
        try:
            cur = conn.execute(
                """SELECT id, title, description, metadata, retry_count
                   FROM tasks
                   WHERE status IN ('todo', 'blocked')
                   AND (tags LIKE '%auto-fix%' OR tags LIKE '%self-heal%')
                   AND (retry_count IS NULL OR retry_count < ?)
                   ORDER BY created_at ASC""",
                (self.max_retries,),
            )
            return [dict(r) for r in cur.fetchall()]
        finally:
            conn.close()

    def _update_task(self, task_id: str, status: str, retry_count: int, logs: str):
        if not Path(self.db_path).exists():
            return
        conn = self._get_db()
        try:
            existing_meta: dict[str, Any] = {}
            row = conn.execute("SELECT metadata FROM tasks WHERE id=?", (task_id,)).fetchone()
            if row and row["metadata"]:
                try:
                    existing_meta = json.loads(row["metadata"])
                except (TypeError, ValueError, json.JSONDecodeError):
                    existing_meta = {}
            meta_update = {
                **existing_meta,
                "last_fix_log": logs[-2000:],
                "last_fix_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
            }
            conn.execute(
                """UPDATE tasks SET status=?, retry_count=?, metadata=?, updated_at=? WHERE id=?""",
                (
                    status,
                    retry_count,
                    json.dumps(meta_update, ensure_ascii=False),
                    time.strftime("%Y-%m-%dT%H:%M:%S"),
                    task_id,
                ),
            )
            conn.commit()
        finally:
            conn.close()

    async def run(self):
        self.running = True
        logger.info(
            f"🤖 AutoFix worker started. DB: {self.db_path} | WS: {self.workspace} | Poll: {self.poll_interval}s"
        )
        while self.running:
            try:
                tasks = self._fetch_pending_tasks()
                if not tasks:
                    await asyncio.sleep(self.poll_interval)
                    continue

                for task in tasks:
                    await self._process_task(task)
                await asyncio.sleep(self.poll_interval)
            except Exception as e:
                logger.error(f"Worker loop error: {e}")
                await asyncio.sleep(self.poll_interval)

    async def _process_task(self, task: dict):
        task_id = task["id"]
        retry = int(task.get("retry_count") or 0)
        logger.info(f"🔧 Processing auto-fix #{task_id} (attempt {retry + 1}/{self.max_retries})")

        if self.dry_run:
            logger.info(f"  [DRY RUN] Would process task {task_id}.")
            return

        snapshot = WorkspaceSnapshot.capture(self.workspace)

        # Step 0: Parse error and try patching
        desc = task.get("description", "")
        patch_res = {"success": False, "logs": "", "actions_taken": []}
        if desc:
            logger.info("  🔍 Analyzing errors and generating patches...")
            patch_res = self.engine.attempt_patch(desc)
            if patch_res.get("success"):
                logger.info(f"    ✅ Patch applied: {patch_res['actions_taken']}")

        # Step 1: Lint & Format
        logger.info("  🧹 Running linters/formatters...")
        lint_res = self.engine.run_lint_fix()

        # Step 2: Run Tests
        logger.info("  🧪 Running tests...")
        test_res = self.engine.run_tests()

        all_logs = (
            patch_res.get("logs", "") + "\n" + lint_res.get("logs", "") + "\n" + test_res.get("logs", "")
        ).strip()
        diff_text = snapshot.diff(self.workspace)
        if diff_text:
            all_logs = (all_logs + "\n\nDiff:\n" + diff_text).strip()

        if lint_res.get("success", True) and test_res.get("success", True):
            logger.info(f"  ✅ Task {task_id} fixed successfully.")
            self._update_task(task_id, "done", retry, all_logs)
        else:
            if diff_text:
                rollback_logs = snapshot.restore(self.workspace)
                all_logs = (all_logs + "\n\nRollback:\n" + "\n".join(rollback_logs)).strip()
            new_retry = retry + 1
            status = "todo" if new_retry < self.max_retries else "failed"
            logger.warning(f"  ❌ Task {task_id} still failing (attempt {new_retry}). Status: {status}")
            self._update_task(task_id, status, new_retry, all_logs)

    def stop(self):
        self.running = False
        logger.info("🛑 AutoFix worker stopping...")


def _binary_cmd(binary: str) -> list[str] | None:
    return [binary] if shutil.which(binary) else None


class WorkspaceSnapshot:
    """Text-file workspace snapshot used to roll back failed auto-fix attempts."""

    def __init__(self, root: Path, files: dict[str, str]):
        self.root = root
        self.files = files

    @classmethod
    def capture(cls, root: Path | str) -> WorkspaceSnapshot:
        root_path = Path(root).resolve()
        files: dict[str, str] = {}
        for path in _iter_snapshot_files(root_path):
            rel = str(path.relative_to(root_path))
            try:
                files[rel] = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
        return cls(root_path, files)

    def diff(self, root: Path | str | None = None) -> str:
        root_path = Path(root).resolve() if root else self.root
        current = WorkspaceSnapshot.capture(root_path)
        chunks = []
        for rel in sorted(set(self.files) | set(current.files)):
            before = self.files.get(rel, "")
            after = current.files.get(rel, "")
            if before == after:
                continue
            chunks.extend(_unified_diff(rel, before, after).splitlines())
        return "\n".join(chunks)

    def restore(self, root: Path | str | None = None) -> list[str]:
        root_path = Path(root).resolve() if root else self.root
        current = WorkspaceSnapshot.capture(root_path)
        logs = []

        for rel, content in self.files.items():
            path = root_path / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
            if current.files.get(rel) != content:
                logs.append(f"restored {rel}")

        for rel in sorted(set(current.files) - set(self.files)):
            path = root_path / rel
            if path.exists():
                path.unlink()
                logs.append(f"removed {rel}")

        return logs or ["no changes to roll back"]


def _iter_snapshot_files(root: Path):
    for path in root.rglob("*"):
        try:
            rel = path.relative_to(root)
        except ValueError:
            continue
        if any(part in SNAPSHOT_EXCLUDES for part in rel.parts):
            continue
        if path.is_file() and path.suffix.lower() in SNAPSHOT_EXTENSIONS:
            yield path


def _unified_diff(path: str, before: str, after: str) -> str:
    return "".join(
        difflib.unified_diff(
            before.splitlines(keepends=True),
            after.splitlines(keepends=True),
            fromfile=f"a/{path}",
            tofile=f"b/{path}",
        )
    ).rstrip()


def _python_module_cmd(module: str) -> list[str] | None:
    try:
        import importlib.util

        if importlib.util.find_spec(module) is None:
            return None
    except (ImportError, ValueError):
        return None
    return [sys.executable, "-m", module]


def _insert_import(content: str, import_stmt: str) -> tuple[str, bool]:
    lines = content.splitlines()
    if import_stmt in lines:
        return content, False

    insert_at = 0
    if lines and lines[0].startswith("#!"):
        insert_at = 1
    if insert_at < len(lines) and "coding" in lines[insert_at]:
        insert_at += 1

    try:
        tree = ast.parse(content)
        if (
            tree.body
            and isinstance(tree.body[0], ast.Expr)
            and isinstance(getattr(tree.body[0], "value", None), ast.Constant)
            and isinstance(tree.body[0].value.value, str)
        ):
            insert_at = max(insert_at, tree.body[0].end_lineno or insert_at)
    except SyntaxError:
        pass

    while insert_at < len(lines) and not lines[insert_at].strip():
        insert_at += 1

    while insert_at < len(lines) and lines[insert_at].startswith("from __future__ import "):
        insert_at += 1

    last_import = None
    scan_at = insert_at
    while scan_at < len(lines):
        line = lines[scan_at]
        if line.startswith(("import ", "from ")):
            last_import = scan_at
            scan_at += 1
            continue
        if not line.strip():
            scan_at += 1
            continue
        break
    if last_import is not None:
        insert_at = last_import + 1

    lines.insert(insert_at, import_stmt)
    trailing_newline = "\n" if content.endswith("\n") else ""
    return "\n".join(lines) + trailing_newline, True


def create_fix_task_from_ci(
    repo: str,
    pr_number: int | None,
    pr_url: str,
    ci_error: str,
    ci_platform: str,
    db_path: str = DEFAULT_KANBAN_DB,
) -> dict[str, Any]:
    """Create an auto-fix Kanban task for a failed CI event."""
    path = _resolve_kanban_db_path(db_path)
    if not path.exists():
        return {
            "success": False,
            "error": f"Kanban DB not found: {path}",
            "suggestion": "Start Hermes Kanban or pass --db to watch-fix.",
        }

    title = f"Auto-fix CI failure: {repo}"
    if pr_number:
        title = f"{title} #{pr_number}"

    description = "\n".join(
        [
            "CI failure detected by Rigor.",
            f"Platform: {ci_platform}",
            f"Repository: {repo}",
            f"PR: {pr_number or 'N/A'}",
            f"URL: {pr_url or 'N/A'}",
            "",
            "Error:",
            ci_error,
        ]
    )
    metadata = {
        "source": "rigor-webhook",
        "repo": repo,
        "pr_number": pr_number,
        "pr_url": pr_url,
        "ci_platform": ci_platform,
    }

    try:
        with closing(sqlite3.connect(path)) as conn:
            conn.row_factory = sqlite3.Row
            columns = {row["name"] for row in conn.execute("PRAGMA table_info(tasks)").fetchall()}
            if not columns:
                return {"success": False, "error": "Kanban DB does not contain a tasks table."}

            now = time.strftime("%Y-%m-%dT%H:%M:%S")
            values: dict[str, Any] = {}
            optional_values = {
                "title": title,
                "description": description,
                "status": "todo",
                "priority": "high",
                "tags": json.dumps(["auto-fix", "self-heal", "ci", ci_platform]),
                "metadata": json.dumps(metadata, ensure_ascii=False),
                "retry_count": 0,
                "created_at": now,
                "updated_at": now,
            }
            for key, value in optional_values.items():
                if key in columns:
                    values[key] = value

            if not {"title", "description"}.issubset(values):
                return {"success": False, "error": "Kanban tasks table lacks title/description columns."}

            placeholders = ", ".join("?" for _ in values)
            col_names = ", ".join(values)
            cur = conn.execute(f"INSERT INTO tasks ({col_names}) VALUES ({placeholders})", tuple(values.values()))
            conn.commit()
            task_id = cur.lastrowid
            return {"success": True, "task_id": task_id}
    except sqlite3.Error as e:
        return {"success": False, "error": str(e)}


def watch_fix(
    db_path: str = DEFAULT_KANBAN_DB,
    workspace: str = ".",
    interval: int = 15,
    max_retries: int = 3,
    dry_run: bool = False,
) -> None:
    """Run the Auto-Fix worker until interrupted."""
    worker = AutoFixWorker(
        str(_resolve_kanban_db_path(db_path)),
        workspace,
        poll_interval=interval,
        max_retries=max_retries,
        dry_run=dry_run,
    )
    try:
        asyncio.run(worker.run())
    except KeyboardInterrupt:
        worker.stop()


def _resolve_kanban_db_path(db_path: str | Path) -> Path:
    path = Path(db_path).expanduser()
    legacy_path = Path(LEGACY_KANBAN_DB).expanduser()
    default_path = Path(DEFAULT_KANBAN_DB).expanduser()
    if path.exists() or path not in {legacy_path, default_path}:
        return path
    for candidate in (default_path, legacy_path):
        if candidate.exists():
            return candidate
    return path
