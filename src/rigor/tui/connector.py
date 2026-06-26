"""Real-time Data Connector for Rigor TUI."""

import sqlite3
import os
from typing import List, Dict, Any
from datetime import datetime


class RigorDataConnector:
    """Reads data from Hermes Kanban and Rigor workspace."""
    
    def __init__(self, hermes_home: str = None):
        self.hermes_home = hermes_home or os.getenv("HERMES_HOME", os.path.expanduser("~/.hermes"))
        self.kanban_db = os.path.join(self.hermes_home, "kanban", "board.db")
        
    def get_kanban_tasks(self) -> Dict[str, List[Dict[str, Any]]]:
        """Read Kanban tasks from SQLite database."""
        tasks = {"todo": [], "doing": [], "done": []}
        if not os.path.exists(self.kanban_db):
            return tasks
            
        try:
            conn = sqlite3.connect(self.kanban_db)
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
                        
            conn.close()
        except Exception as e:
            print(f"DB Error: {e}")
            
        return tasks

    def get_agent_status(self) -> Dict[str, str]:
        """Get current status of each agent profile."""
        profiles_dir = os.path.join(self.hermes_home, "profiles")
        agents = [
            "orchestrator", "product-manager", "tech-lead",
            "backend-engineer", "frontend-engineer", "qa-engineer",
            "security-auditor", "devops-engineer", "technical-writer"
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

    def get_metrics(self) -> Dict[str, Any]:
        """Get cost and token metrics (simulated for now)."""
        # TODO: Implement real token counting from logs or API
        return {
            "tokens_in": 0,
            "tokens_out": 0,
            "cost": 0.0
        }
