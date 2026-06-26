"""Auto-Fix Loop: Autonomous self-healing background worker for Rigor Kanban.

Combines:
1. Kanban task polling for `auto-fix` tagged tasks
2. Error parsing & deterministic patch generation
3. Lint/fix execution
4. Test execution & validation
5. Task status updates with retry limits
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
import sqlite3
import subprocess
import time
from pathlib import Path
from typing import Dict, List

from rigor.core.file_ops import FileOps
from rigor.core.patch_gen import ErrorParser, PatchGenerator

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("rigor.autofix")


class ProjectDetector:
    @staticmethod
    def detect(workspace: Path) -> str:
        if (workspace / "pyproject.toml").exists() or (workspace / "requirements.txt").exists() or (workspace / "setup.py").exists():
            return "python"
        if (workspace / "package.json").exists():
            return "node"
        if (workspace / "go.mod").exists():
            return "go"
        if (workspace / "Cargo.toml").exists():
            return "rust"
        return "unknown"


class AutoFixEngine:
    def __init__(self, workspace: Path):
        self.workspace = workspace
        self.project_type = ProjectDetector.detect(workspace)
        self.file_ops = FileOps(str(workspace))
        self.patch_gen = PatchGenerator(self.file_ops)

    def run_lint_fix(self) -> Dict:
        cmds: List[List[str]] = []
        if self.project_type == "python":
            cmds = [["ruff", "check", "--fix", "."], ["ruff", "format", "."]]
        elif self.project_type == "node":
            cmds = [["npx", "eslint", ".", "--fix", "--quiet"], ["npx", "prettier", ".", "--write", "--log-level", "warn"]]
        elif self.project_type == "go":
            cmds = [["go", "fmt", "./..."], ["golangci-lint", "run", "--fix"]]

        logs: List[str] = []
        success = True
        for cmd in cmds:
            try:
                res = subprocess.run(cmd, cwd=self.workspace, capture_output=True, text=True, timeout=30)
                logs.append(f"$ {' '.join(cmd)}\n{res.stdout}\n{res.stderr}")
                if res.returncode not in (0, 1):
                    success = False
            except FileNotFoundError:
                logs.append(f"[WARN] {cmd[0]} not found. Skipping.")
            except Exception as e:
                logs.append(f"[ERROR] {cmd[0]} failed: {e}")
                success = False

        return {"success": success, "logs": "\n".join(logs), "actions_taken": ["lint_fix"]}

    def run_tests(self) -> Dict:
        cmds: List[str] = []
        if self.project_type == "python":
            if (self.workspace / "pytest.ini").exists() or (self.workspace / "pyproject.toml").exists():
                cmds = ["pytest", "--tb=short", "-q", "--last-failed"]
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

    def attempt_patch(self, error_output: str) -> Dict:
        """Parse errors and generate/apply patches."""
        issues = ErrorParser.parse(error_output)
        if not issues:
            return {"success": False, "logs": "No specific issues found to patch.", "actions_taken": []}

        logs = []
        actions = []
        for issue in issues:
            logger.info(f"  📝 Fixing {issue['file']}:{issue['line']} - {issue['message']}")
            patch = self.patch_gen.generate_patch(issue["file"], issue["line"], issue["message"])
            if patch:
                try:
                    current_content = self.file_ops.read_file(issue["file"])
                    # Apply patch (simplified: prepend import, replace line, etc.)
                    if patch.startswith("import ") or patch.startswith("from "):
                        # Insert import at top of file
                        lines = current_content.split("\n")
                        for i, l in enumerate(lines):
                            if l.startswith("import ") or l.startswith("from ") or (l.startswith("#") and i < 5):
                                continue
                            lines.insert(i, patch)
                            break
                        self.file_ops.write_file(issue["file"], "\n".join(lines))
                        logs.append(f"✅ Applied import: {patch}")
                        actions.append("patch_import")
                    else:
                        logs.append(f"💡 Suggestion: {patch}")
                        actions.append("suggestion")
                except Exception as e:
                    logs.append(f"❌ Patch failed: {e}")

        return {"success": len(actions) > 0, "logs": "\n".join(logs), "actions_taken": actions}


class AutoFixWorker:
    def __init__(self, db_path: str, workspace: str, poll_interval: int = 15, max_retries: int = 3, dry_run: bool = False):
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

    def _fetch_pending_tasks(self) -> List[dict]:
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
            meta_update = {"last_fix_log": logs[-2000:], "last_fix_at": time.strftime("%Y-%m-%dT%H:%M:%S")}
            conn.execute(
                """UPDATE tasks SET status=?, retry_count=?, metadata=?, updated_at=? WHERE id=?""",
                (status, retry_count, json.dumps(meta_update), time.strftime("%Y-%m-%dT%H:%M:%S"), task_id),
            )
            conn.commit()
        finally:
            conn.close()

    async def run(self):
        self.running = True
        logger.info(f"🤖 AutoFix worker started. DB: {self.db_path} | WS: {self.workspace} | Poll: {self.poll_interval}s")
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

        all_logs = (patch_res.get("logs", "") + "\n" + lint_res.get("logs", "") + "\n" + test_res.get("logs", "")).strip()

        if test_res.get("success", True):
            logger.info(f"  ✅ Task {task_id} fixed successfully.")
            self._update_task(task_id, "done", retry, all_logs)
        else:
            new_retry = retry + 1
            status = "todo" if new_retry < self.max_retries else "failed"
            logger.warning(f"  ❌ Task {task_id} still failing (attempt {new_retry}). Status: {status}")
            self._update_task(task_id, status, new_retry, all_logs)

    def stop(self):
        self.running = False
        logger.info("🛑 AutoFix worker stopping...")
