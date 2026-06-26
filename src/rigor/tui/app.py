"""
Rigor TUI v2.1 - Interactive k9s-style dashboard for Rigor AI Engineering Team.

Features:
- Real-time data from Hermes Kanban DB
- Multi-view switching (Monitor, Logs, Settings)
- Interactive Kanban board (select, view details)
- Agent status matrix with live updates
- Token/Cost monitoring
"""

import os
import time
import asyncio
from typing import List, Dict, Any

from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static, Input, RichLog, DataTable, Label
from textual.containers import Container, Horizontal, Vertical, Grid
from textual.screen import Screen
from textual.binding import Binding
from textual.reactive import reactive
from textual import work

try:
    from src.rigor.tui.connector import RigorDataConnector
except ImportError:
    from .connector import RigorDataConnector

# Constants
AGENT_ICONS = {
    "orchestrator": "🎯",
    "product-manager": "📋",
    "tech-lead": "🏗️",
    "backend-engineer": "⚙️",
    "frontend-engineer": "🎨",
    "qa-engineer": "✅",
    "security-auditor": "🛡️",
    "devops-engineer": "🚀",
    "technical-writer": "📝",
}


class MonitorScreen(Screen):
    """Main monitoring dashboard screen."""
    
    BINDINGS = [
        Binding("q", "app.quit", "Quit"),
        Binding("l", "focus_input", "Input"),
        Binding("1", "show_monitor", "Monitor"),
        Binding("2", "show_logs", "Logs"),
        Binding("3", "show_settings", "Settings"),
    ]
    
    def __init__(self, connector: RigorDataConnector):
        super().__init__()
        self.connector = connector
        self.agent_widgets = {}

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Horizontal(id="main-layout"):
            # Left: Input & Log
            with Vertical(id="left-panel"):
                yield Label("📝 Command Input", classes="panel-title")
                yield Input(placeholder="Type command... (e.g. 'rigor scan')", id="cmd-input")
                yield Label("📜 Event Log", classes="panel-title")
                yield RichLog(id="log-viewer", highlight=True, markup=True)

            # Right: Kanban & Agents & Metrics
            with Vertical(id="right-panel"):
                # Agent Grid
                yield Label("🤖 Agent Status", classes="panel-title")
                with Grid(id="agent-grid"):
                    pass  # Populated in on_mount

                # Kanban Board
                yield Label("📋 Kanban Board", classes="panel-title")
                yield DataTable(id="kanban-table")

                # Metrics
                yield Label("💰 Metrics", classes="panel-title")
                yield Static(id="metrics-panel", classes="metrics-box")

        yield Footer()

    def on_mount(self) -> None:
        # Populate agent grid
        grid = self.query_one("#agent-grid")
        for agent_name, icon in AGENT_ICONS.items():
            w = AgentStatusWidget(agent_name, icon)
            self.agent_widgets[agent_name] = w
            grid.mount(w)

        # Init Kanban table
        table = self.query_one("#kanban-table")
        table.add_columns("ID", "Status", "Task", "Assignee")
        
        # Start background worker for real-time updates
        self.run_worker(self.update_loop, exclusive=True)
        self.log_info("System initialized. Ready.")

    async def update_loop(self):
        """Periodically update UI from data source."""
        while self.is_running:
            agents = self.connector.get_agent_status()
            self.update_agents(agents)
            
            tasks = self.connector.get_kanban_tasks()
            self.update_kanban(tasks)
            
            metrics = self.connector.get_metrics()
            self.update_metrics(metrics)
            
            await asyncio.sleep(2)

    def update_agents(self, statuses: Dict[str, str]):
        for name, status in statuses.items():
            if name in self.agent_widgets:
                self.agent_widgets[name].update(status)

    def update_kanban(self, tasks: Dict[str, List[Dict]]):
        table = self.query_one("#kanban-table")
        table.clear()
        for status, task_list in tasks.items():
            for task in task_list:
                tid = task.get("id", "?")[:6]
                title = task.get("title", "Untitled")[:20]
                assignee = task.get("assignee", "Unassigned")
                icon = "📥" if status == "todo" else ("🔄" if status == "doing" else "✅")
                table.add_row(tid, icon, title, assignee)

    def update_metrics(self, metrics: Dict[str, Any]):
        panel = self.query_one("#metrics-panel")
        cost_bar_len = min(20, int(metrics.get("cost", 0) * 2))
        cost_bar = "█" * cost_bar_len + "░" * (20 - cost_bar_len)
        color = "red" if metrics.get("cost", 0) > 50 else "green"
        
        panel.update(
            f"Input Tokens: {metrics.get('tokens_in', 0):,}\n"
            f"Output Tokens: {metrics.get('tokens_out', 0):,}\n"
            f"Cost: [{color}]${metrics.get('cost', 0):.2f}[/] {cost_bar}"
        )

    def on_input_submitted(self, event: Input.Submitted):
        log = self.query_one("#log-viewer")
        cmd = event.value.strip()
        if not cmd: return
        event.value = ""
        
        log.write(f"[bold green]$ {cmd}[/]")
        # Simulate command execution
        log.write(f"[dim]Processing... Done.[/]")

    def action_focus_input(self):
        self.query_one("#cmd-input").focus()
        
    def log_info(self, msg):
        if self.is_mounted:
            self.query_one("#log-viewer").write(f"[cyan][INFO][/] {msg}")
            
    def action_show_monitor(self):
        self.notify("Already on Monitor view")
        
    def action_show_logs(self):
        self.app.push_screen("log_screen")
        
    def action_show_settings(self):
        self.notify("Settings view not yet implemented")


class LogScreen(Screen):
    """Log viewer screen."""
    BINDINGS = [Binding("escape", "app.pop_screen", "Back")]
    
    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Label("📜 Full Log Viewer", classes="panel-title")
        yield RichLog(id="full-log", highlight=True, markup=True)
        yield Footer()

    def on_mount(self):
        log = self.query_one("#full-log")
        log.write("[yellow]Log stream initialized...[/]")
        # TODO: Tail real log files here


class AgentStatusWidget(Static):
    """Displays a single agent status."""
    def __init__(self, name, icon):
        super().__init__(f"{icon} {name}: 🟢 Idle", classes="agent-widget")
        self.agent_name = name
        
    def update(self, status: str):
        self.update(f"{AGENT_ICONS.get(self.agent_name, '❓')} {self.agent_name}: {status}")
        if "🟡" in status:
            self.styles.color = "yellow"
        elif "🔴" in status:
            self.styles.color = "red"
        elif "⚫" in status:
            self.styles.color = "grey"
        else:
            self.styles.color = "green"


class RigorTUIApp(App):
    """Main Application."""
    CSS_PATH = "style.tcss"
    SCREENS = {
        "monitor": MonitorScreen,
        "log_screen": LogScreen,
    }
    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("f2", "push_screen('log_screen')", "Logs"),
    ]
    
    def on_mount(self) -> None:
        connector = RigorDataConnector()
        self.push_screen(MonitorScreen(connector))


if __name__ == "__main__":
    app = RigorTUIApp()
    app.run()
