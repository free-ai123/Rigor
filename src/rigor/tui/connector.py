"""Real-time Data Connector for Rigor TUI."""

import os
import shutil
import sqlite3
import subprocess
from contextlib import closing
from datetime import datetime
from pathlib import Path
from typing import Any


class RigorDataConnector:
    """Reads data from Hermes Kanban and Rigor workspace."""

    def __init__(self, hermes_home: str | None = None, workspace: str | Path | None = None):
        self.hermes_home = hermes_home or os.getenv("HERMES_HOME", os.path.expanduser("~/.hermes"))
        self.kanban_db = str(resolve_kanban_db_path(self.hermes_home))
        self.workspace = Path(workspace or os.getenv("RIGOR_WORKSPACE", os.getcwd())).resolve()

    def get_kanban_tasks(self) -> dict[str, list[dict[str, Any]]]:
        """Read Kanban tasks from SQLite database."""
        tasks = {"todo": [], "doing": [], "done": []}
        if not os.path.exists(self.kanban_db):
            return tasks

        try:
            with closing(sqlite3.connect(self.kanban_db)) as conn:
                conn.row_factory = sqlite3.Row
                cur = conn.cursor()

                # Try to read tasks table (schema may vary)
                cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [row[0] for row in cur.fetchall()]

                if "tasks" in tables:
                    cur.execute("SELECT * FROM tasks ORDER BY created_at DESC LIMIT 50")
                    for row in cur.fetchall():
                        task = dict(row)
                        status = task.get("status", "todo").lower()
                        if status in tasks:
                            tasks[status].append(task)
                        elif "in_progress" in status or "working" in status:
                            tasks["doing"].append(task)
        except Exception as e:
            print(f"DB Error: {e}")

        return tasks

    def get_agent_status(self) -> dict[str, str]:
        """Get current status of each agent profile."""
        profiles_dir = os.path.join(self.hermes_home, "profiles")
        agents = [
            "orchestrator",
            "product-manager",
            "tech-lead",
            "backend-engineer",
            "frontend-engineer",
            "data-scientist",
            "data-engineer",
            "code-reviewer",
            "qa-engineer",
            "security-auditor",
            "devops-engineer",
            "technical-writer",
        ]

        status = {}
        for agent in agents:
            profile_dir = os.path.join(profiles_dir, agent)
            if os.path.exists(profile_dir):
                # Check for active sessions
                sessions_dir = os.path.join(profile_dir, "sessions")
                if os.path.exists(sessions_dir):
                    sessions = os.listdir(sessions_dir)
                    if sessions:
                        # Sort by modification time
                        sessions.sort(key=lambda x: os.path.getmtime(os.path.join(sessions_dir, x)), reverse=True)
                        latest = sessions[0]
                        mtime = os.path.getmtime(os.path.join(sessions_dir, latest))
                        age = datetime.now().timestamp() - mtime

                        if age < 60:
                            status[agent] = "🟡 Working"
                        else:
                            status[agent] = "🟢 Idle"
                    else:
                        status[agent] = "🟢 Idle"
                else:
                    status[agent] = "🟢 Idle"
            else:
                status[agent] = "⚫ Not Installed"

        return status

    def get_metrics(self) -> dict[str, Any]:
        """Get cost and token metrics."""
        result = _run(["hermes", "insights", "--days", "1", "--json"], timeout=5)
        if result and result.stdout.strip():
            try:
                import json

                data = json.loads(result.stdout)
                tokens_in = int(data.get("total_input_tokens", 0))
                tokens_out = int(data.get("total_output_tokens", 0))
                return {
                    "tokens_in": tokens_in,
                    "tokens_out": tokens_out,
                    "cost": _estimate_cost(tokens_in, tokens_out),
                }
            except (TypeError, ValueError):
                pass

        return {"tokens_in": 0, "tokens_out": 0, "cost": 0.0}


def _run(args: list[str], timeout: int = 5) -> subprocess.CompletedProcess[str] | None:
    if not args or shutil.which(args[0]) is None:
        return None
    try:
        return subprocess.run(args, capture_output=True, text=True, timeout=timeout)
    except Exception:
        return None


def _estimate_cost(input_tokens: int, output_tokens: int) -> float:
    return input_tokens * 3 / 1_000_000 + output_tokens * 15 / 1_000_000


def resolve_kanban_db_path(hermes_home: str | Path) -> Path:
    home = Path(hermes_home).expanduser()
    candidates = [
        home / "kanban.db",
        home / "kanban" / "board.db",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]
