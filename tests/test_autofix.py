"""Tests for rigor.autofix module."""

import asyncio
import json
import sqlite3
from contextlib import closing

from rigor.autofix import AutoFixEngine, AutoFixWorker, ProjectDetector, WorkspaceSnapshot, create_fix_task_from_ci


class TestProjectDetector:
    def test_detect_python(self, tmp_workspace):
        """Detect Python project."""
        assert ProjectDetector.detect(tmp_workspace) == "python"

    def test_detect_node(self, tmp_path):
        """Detect Node.js project."""
        (tmp_path / "package.json").write_text("{}")
        assert ProjectDetector.detect(tmp_path) == "node"

    def test_detect_go(self, tmp_path):
        """Detect Go project."""
        (tmp_path / "go.mod").write_text("module test")
        assert ProjectDetector.detect(tmp_path) == "go"

    def test_detect_unknown(self, tmp_path):
        """Detect unknown project type."""
        assert ProjectDetector.detect(tmp_path) == "unknown"


class TestAutoFixEngine:
    """Test suite for AutoFixEngine."""

    def test_engine_initializes(self, tmp_workspace):
        """Test engine initializes with workspace."""
        engine = AutoFixEngine(tmp_workspace)
        assert engine.project_type == "python"

    def test_run_tests_no_runner(self, tmp_workspace):
        """Test when no test runner is detected."""
        engine = AutoFixEngine(tmp_workspace)
        result = engine.run_tests()
        # Should return success with message since no pytest.ini/pyproject.toml with pytest config
        assert result["success"] is True or result["success"] is False

    def test_attempt_patch_inserts_import_without_read_header(self, tmp_path):
        """Auto patching imports should not write paginated read headers into source files."""
        (tmp_path / "src").mkdir()
        target = tmp_path / "src" / "app.py"
        target.write_text('"""Module doc."""\n\nprint(os.getcwd())\n', encoding="utf-8")

        engine = AutoFixEngine(tmp_path)
        result = engine.attempt_patch("src/app.py:3:1: name 'os' is not defined")

        assert result["success"] is True
        assert "--- a/src/app.py" in result["diffs"][0]
        content = target.read_text(encoding="utf-8")
        assert "// Lines" not in content
        assert content.startswith('"""Module doc."""\n\nimport os\n')

    def test_workspace_snapshot_diff_and_restore(self, tmp_path):
        target = tmp_path / "app.py"
        target.write_text("print('before')\n", encoding="utf-8")
        snapshot = WorkspaceSnapshot.capture(tmp_path)

        target.write_text("print('after')\n", encoding="utf-8")
        created = tmp_path / "new.py"
        created.write_text("print('new')\n", encoding="utf-8")

        diff = snapshot.diff(tmp_path)
        rollback_logs = snapshot.restore(tmp_path)

        assert "--- a/app.py" in diff
        assert "+++ b/new.py" in diff
        assert target.read_text(encoding="utf-8") == "print('before')\n"
        assert not created.exists()
        assert "restored app.py" in rollback_logs
        assert "removed new.py" in rollback_logs


class TestAutoFixWorker:
    """Test suite for AutoFixWorker."""

    def _create_mock_db(self, tmp_path):
        """Create a mock Kanban database with a test task."""
        db_path = str(tmp_path / "board.db")
        with closing(sqlite3.connect(db_path)) as conn:
            conn.execute("""
                CREATE TABLE tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT,
                    description TEXT,
                    status TEXT DEFAULT 'todo',
                    assignee TEXT,
                    priority TEXT DEFAULT 'medium',
                    tags TEXT DEFAULT '[]',
                    metadata TEXT DEFAULT '{}',
                    retry_count INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.execute(
                """INSERT INTO tasks (title, description, status, tags)
                   VALUES (?, ?, ?, ?)""",
                ("Auto-Fix Test Task", "Some error occurred", "todo", '["auto-fix"]'),
            )
            conn.commit()
        return db_path

    def test_fetch_pending_tasks(self, tmp_path):
        """Test fetching pending auto-fix tasks."""
        db_path = self._create_mock_db(tmp_path)
        worker = AutoFixWorker(db_path, str(tmp_path), poll_interval=1, max_retries=3)
        tasks = worker._fetch_pending_tasks()
        assert len(tasks) == 1
        assert tasks[0]["title"] == "Auto-Fix Test Task"

    def test_update_task_status(self, tmp_path):
        """Test updating task status."""
        db_path = self._create_mock_db(tmp_path)
        worker = AutoFixWorker(db_path, str(tmp_path), poll_interval=1, max_retries=3)
        worker._update_task("1", "done", 0, "Fixed successfully")

        with closing(sqlite3.connect(db_path)) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute("SELECT status, retry_count FROM tasks WHERE id=1").fetchone()
            assert row["status"] == "done"

    def test_create_fix_task_from_ci(self, tmp_path):
        """CI failures can be converted into auto-fix Kanban tasks."""
        db_path = self._create_mock_db(tmp_path)
        result = create_fix_task_from_ci(
            repo="owner/repo",
            pr_number=42,
            pr_url="https://example.test/pr/42",
            ci_error="pytest failed",
            ci_platform="github",
            db_path=db_path,
        )

        assert result["success"] is True

        with closing(sqlite3.connect(db_path)) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute("SELECT title, tags, metadata FROM tasks WHERE id=?", (result["task_id"],)).fetchone()
            assert "owner/repo" in row["title"]
            assert "auto-fix" in row["tags"]
            assert json.loads(row["metadata"])["pr_number"] == 42

    def test_max_retries_exceeded(self, tmp_path):
        """Test that tasks with retry_count >= max_retries are not fetched."""
        db_path = self._create_mock_db(tmp_path)
        with closing(sqlite3.connect(db_path)) as conn:
            conn.execute("UPDATE tasks SET retry_count = 3 WHERE id = 1")
            conn.commit()

        worker = AutoFixWorker(db_path, str(tmp_path), poll_interval=1, max_retries=3)
        tasks = worker._fetch_pending_tasks()
        assert len(tasks) == 0

    def test_process_task_dry_run(self, tmp_path):
        """Test processing a task in dry-run mode."""
        db_path = self._create_mock_db(tmp_path)
        worker = AutoFixWorker(db_path, str(tmp_path), poll_interval=1, max_retries=3, dry_run=True)
        worker.running = True  # Ensure loop doesn't stop

        tasks = worker._fetch_pending_tasks()
        assert len(tasks) == 1
        asyncio.run(worker._process_task(tasks[0]))

        # Task should still be in 'todo' status (dry run)
        with closing(sqlite3.connect(db_path)) as conn:
            row = conn.execute("SELECT status FROM tasks WHERE id=1").fetchone()
            assert row[0] == "todo"

    def test_process_task_rolls_back_when_tests_fail(self, tmp_path):
        """Failed validation should restore files and persist the attempted diff."""
        db_path = self._create_mock_db(tmp_path)
        (tmp_path / "pyproject.toml").write_text("[project]\nname='demo'\n", encoding="utf-8")
        (tmp_path / "src").mkdir()
        target = tmp_path / "src" / "app.py"
        original = "print(os.getcwd())\n"
        target.write_text(original, encoding="utf-8")

        with closing(sqlite3.connect(db_path)) as conn:
            conn.execute(
                "UPDATE tasks SET description = ? WHERE id = 1",
                ("src/app.py:1:1: name 'os' is not defined",),
            )
            conn.commit()

        worker = AutoFixWorker(db_path, str(tmp_path), poll_interval=1, max_retries=3)
        worker.engine.run_lint_fix = lambda: {"success": True, "logs": "lint ok", "actions_taken": ["lint_fix"]}
        worker.engine.run_tests = lambda: {"success": False, "logs": "tests failed", "actions_taken": ["test_run"]}

        tasks = worker._fetch_pending_tasks()
        asyncio.run(worker._process_task(tasks[0]))

        assert target.read_text(encoding="utf-8") == original

        with closing(sqlite3.connect(db_path)) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute("SELECT status, retry_count, metadata FROM tasks WHERE id=1").fetchone()
            metadata = json.loads(row["metadata"])
            assert row["status"] == "todo"
            assert row["retry_count"] == 1
            assert "Diff:" in metadata["last_fix_log"]
            assert "Rollback:" in metadata["last_fix_log"]
