"""Auto-Fix Loop: Autonomous self-healing worker for Rigor Kanban."""

from __future__ import annotations
import asyncio
import json
import logging
import os
import re
import sqlite3
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, List, Dict, Any

import click

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("rigor.autofix")


@dataclass
class FixResult:
    success: bool
    logs: str
    actions_taken: List[str] = None

    def __post_init__(self):
        if self.actions_taken is None:
            self.actions_taken = []


class ProjectDetector:
    """Detect project type from workspace root."""

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
    """Executes deterministic self-healing strategies."""

    def __init__(self, workspace: Path):
        self.workspace = workspace
        self.project_type = ProjectDetector.detect(workspace)

    def run_lint_fix(self) -> FixResult:
        """Run auto-formatters/linters based on project type."""
        cmds = []
        if self.project_type == "python":
            cmds = [
                ["ruff", "check", "--fix", "."],
                ["ruff", "format", "."],
            ]
        elif self.project_type == "node":
            cmds = [
                ["npx", "eslint", ".", "--fix", "--quiet"],
                ["npx", "prettier", ".", "--write", "--log-level", "warn"],
            ]
        elif self.project_type == "go":
            cmds = [["go", "fmt", "./..."], ["golangci-lint", "run", "--fix"]]
        elif self.project_type == "rust":
            cmds = [["cargo", "fmt"], ["cargo", "clippy", "--fix", "--allow-dirty"]]

        if not cmds:
            return FixResult(success=True, logs="No linters configured for this project type.", actions_taken=[])

        logs = []
        for cmd in cmds:
            try:
                res = subprocess.run(cmd, cwd=self.workspace, capture_output=True, text=True, timeout=30)
                logs.append(f"$ {' '.join(cmd)}\n{res.stdout}\n{res.stderr}")
            except FileNotFoundError:
                logs.append(f"[WARN] {cmd[0]} not found. Skipping.")
            except Exception as e:
                logs.append(f"[ERROR] {cmd[0]} failed: {e}")

        return FixResult(success=True, logs="\n".join(logs), actions_taken=["lint_fix"])

    def run_tests(self) -> FixResult:
        """Run tests and capture results."""
        cmds = []
        if self.project_type == "python":
            if (self.workspace / "pytest.ini").exists() or (self.workspace / "pyproject.toml").exists():
                cmds = ["pytest", "--tb=short", "-q", "--last-failed"]
        elif self.project_type == "node":
            cmds = ["npm", "test"]
        elif self.project_type == "go":
            cmds = ["go", "test", "./..."]
        elif self.project_type == "rust":
            cmds = ["cargo", "test"]

        if not cmds:
            return FixResult(success=True, logs="No test runner detected.", actions_taken=[])

        try:
            res = subprocess.run(cmds, cwd=self.workspace, capture_output=True, text=True, timeout=120)
            return FixResult(
                success=res.returncode == 0,
                logs=f"$ {' '.join(cmds)}\n{res.stdout}\n{res.stderr}",
                actions_taken=["test_run"],
            )
        except Exception as e:
            return FixResult(success=False, logs=f"Test runner failed: {e}", actions_taken=[])


class AutoFixWorker:
    """Background worker that polls Kanban and executes fixes."""

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
            meta_update = {"last_fix_log": logs, "last_fix_at": time.strftime("%Y-%m-%dT%H:%M:%S")}
            cur = conn.execute(
                """UPDATE tasks SET status=?, retry_count=?, metadata=?, updated_at=? 
                   WHERE id=?""",
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
        retry = task.get("retry_count") or 0
        logger.info(f"🔧 Processing auto-fix #{task_id} (attempt {retry + 1}/{self.max_retries})")

        if self.dry_run:
            logger.info(f"  [DRY RUN] Would process task {task_id}. Metadata: {task.get('metadata', '{}')}")
            return

        # Step 1: Lint & Format
        logger.info("  🧹 Running linters/formatters...")
        lint_res = self.engine.run_lint_fix()
        logger.info(f"    Lint: {'✅' if lint_res.success else '⚠️'} {len(lint_res.actions_taken)} actions")

        # Step 2: Run Tests
        logger.info("  🧪 Running tests...")
        test_res = self.engine.run_tests()

        if test_res.success:
            logger.info(f"  ✅ Task {task_id} fixed successfully.")
            self._update_task(task_id, "done", retry, lint_res.logs + "\n" + test_res.logs)
        else:
            new_retry = retry + 1
            status = "todo" if new_retry < self.max_retries else "failed"
            logger.warning(f"  ❌ Task {task_id} still failing (attempt {new_retry}). Status: {status}")
            self._update_task(task_id, status, new_retry, lint_res.logs + "\n" + test_res.logs)

    def stop(self):
        self.running = False
        logger.info("🛑 AutoFix worker stopping...")


@click.command()
@click.option("--db", default="~/.hermes/kanban/board.db", help="Path to Kanban SQLite DB")
@click.option("--workspace", default=".", help="Project workspace root")
@click.option("--interval", default=15, type=int, help="Poll interval in seconds")
@click.option("--max-retries", default=3, type=int, help="Max auto-fix attempts per task")
@click.option("--dry-run", is_flag=True, help="Simulate fixes without writing to DB")
def watch_fix(db: str, workspace: str, interval: int, max_retries: int, dry_run: bool):
    """🤖 Start the Auto-Fix background daemon."""
    db_path = os.path.expanduser(db)
    worker = AutoFixWorker(db_path, workspace, interval, max_retries, dry_run)
    try:
        asyncio.run(worker.run())
    except KeyboardInterrupt:
        worker.stop()
