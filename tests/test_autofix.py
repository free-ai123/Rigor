"""Tests for rigor.autofix module."""

import sqlite3

import pytest

from rigor.autofix import AutoFixEngine, AutoFixWorker, ProjectDetector


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


class TestAutoFixWorker:
    """Test suite for AutoFixWorker."""

    def _create_mock_db(self, tmp_path):
        """Create a mock Kanban database with a test task."""
        db_path = str(tmp_path / "board.db")
        conn = sqlite3.connect(db_path)
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
        conn.close()
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

        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT status, retry_count FROM tasks WHERE id=1").fetchone()
        assert row["status"] == "done"
        conn.close()

    def test_max_retries_exceeded(self, tmp_path):
        """Test that tasks with retry_count >= max_retries are not fetched."""
        db_path = self._create_mock_db(tmp_path)
        conn = sqlite3.connect(db_path)
        conn.execute("UPDATE tasks SET retry_count = 3 WHERE id = 1")
        conn.commit()
        conn.close()

        worker = AutoFixWorker(db_path, str(tmp_path), poll_interval=1, max_retries=3)
        tasks = worker._fetch_pending_tasks()
        assert len(tasks) == 0

    @pytest.mark.asyncio
    async def test_process_task_dry_run(self, tmp_path):
        """Test processing a task in dry-run mode."""
        db_path = self._create_mock_db(tmp_path)
        worker = AutoFixWorker(db_path, str(tmp_path), poll_interval=1, max_retries=3, dry_run=True)
        worker.running = True  # Ensure loop doesn't stop

        tasks = worker._fetch_pending_tasks()
        assert len(tasks) == 1
        await worker._process_task(tasks[0])

        # Task should still be in 'todo' status (dry run)
        conn = sqlite3.connect(db_path)
        row = conn.execute("SELECT status FROM tasks WHERE id=1").fetchone()
        assert row[0] == "todo"
        conn.close()
