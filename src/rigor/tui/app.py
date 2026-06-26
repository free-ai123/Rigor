"""
Rigor TUI - A k9s-like terminal dashboard for Rigor AI Engineering Team.
Built with Textual (https://textual.textualize.io/).
"""

import time
import random
import asyncio
from typing import List, Dict, Any

try:
    from textual.app import App, ComposeResult
    from textual.widgets import Header, Footer, Static, Input, RichLog, DataTable
    from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
    from textual.reactive import reactive
    from textual import work
    from textual.binding import Binding
    TEXTUAL_AVAILABLE = True
except ImportError:
    TEXTUAL_AVAILABLE = False


# --- Mock Data Sources (Replace with real API calls later) ---
AGENTS = [
    ("orchestrator", "🎯"), ("product-manager", "📋"), ("tech-lead", "🏗️"),
    ("backend-engineer", "⚙️"), ("frontend-engineer", "🎨"), ("qa-engineer", "✅"),
    ("security-auditor", "🛡️"), ("devops-engineer", "🚀"), ("technical-writer", "📝")
]

class MockDataSource:
    """Simulates real-time data updates for Kanban, Agents, and Metrics."""
    
    def __init__(self):
        self.kanban_tasks = {
            "todo": ["Define API schema", "Setup CI/CD pipeline", "Database migration"],
            "doing": ["Implement Auth Service", "Frontend Dashboard Layout"],
            "done": ["Project Init", "Requirements Analysis", "Tech Stack Selection"]
        }
        self.agent_status = {name: random.choice(["🟢 Idle", "🟡 Working", "🔴 Error"]) for name, _ in AGENTS}
        self.metrics = {"tokens_in": 0, "tokens_out": 0, "cost": 0.0}
        
    def update(self):
        # Simulate random changes
        if random.random() > 0.7:
            agent = random.choice(list(self.agent_status.keys()))
            self.agent_status[agent] = random.choice(["🟢 Idle", "🟡 Working", "🔴 Error"])
        
        self.metrics["tokens_in"] += random.randint(100, 500)
        self.metrics["tokens_out"] += random.randint(50, 200)
        self.metrics["cost"] += random.uniform(0.01, 0.05)
        
        return self.kanban_tasks, self.agent_status, self.metrics


class AgentWidget(Static):
    """Displays a single agent's status."""
    def __init__(self, name: str, icon: str, status: str, **kwargs):
        super().__init__(**kwargs)
        self.agent_name = name
        self.icon = icon
        self.update_status(status)
        
    def update_status(self, status: str):
        self._status = status
        color = "green" if "🟢" in status else ("yellow" if "🟡" in status else "red")
        self.styles.color = color
        self.renderable = f"{self.icon} {self.agent_name.replace('-', ' ')}: {status}"


class RigorTUI(App):
    """Main TUI Application."""
    
    CSS = """
    Screen {
        layout: grid;
        grid-size: 2;
        grid-columns: 2fr 1fr;
        grid-rows: 1fr;
    }
    
    #left-panel {
        dock: left;
        width: 100%;
        height: 100%;
        border: tall $primary;
        padding: 1;
    }
    
    #right-panel {
        dock: right;
        width: 100%;
        height: 100%;
        border: tall $success;
        padding: 1;
    }
    
    #command-input {
        dock: bottom;
        height: 3;
        margin-top: 1;
    }
    
    #log-viewer {
        height: 1fr;
        background: $surface;
    }
    
    #agent-grid {
        height: 1fr;
        content-align: center top;
    }
    
    #kanban-board {
        height: 1fr;
        margin-top: 1;
    }
    
    #metrics-panel {
        height: auto;
        margin-top: 1;
        padding: 1;
        background: $boost;
    }
    
    .agent-item {
        width: 100%;
        height: 1;
    }
    """
    
    BINDINGS = [
        Binding("q", "quit", "Quit", priority=True),
        Binding("ctrl+g", "focus_input", "Input"),
    ]
    
    def __init__(self):
        super().__init__()
        self.data_source = MockDataSource()
        self.agent_widgets = {}
        
    def compose(self) -> ComposeResult:
        yield Header(id="header")
        
        with Horizontal():
            with Vertical(id="left-panel"):
                yield Static("📝 Command History", classes="panel-title")
                yield RichLog(id="log-viewer", highlight=True, markup=True)
                yield Input(placeholder="Type a command... (e.g. 'rigor scan')", id="command-input")
            
            with Vertical(id="right-panel"):
                yield Static("🤖 Agent Status", classes="panel-title")
                yield Container(id="agent-grid") # Will be populated dynamically
                yield Static("📋 Kanban Board", classes="panel-title")
                yield DataTable(id="kanban-board")
                yield Static("💰 Metrics", classes="panel-title")
                yield Static(id="metrics-panel")
                
        yield Footer()

    def on_mount(self) -> None:
        """Initialize data and start the update loop."""
        # Initialize Agent Grid
        grid = self.query_one("#agent-grid")
        for name, icon in AGENTS:
            w = AgentWidget(name, icon, "🟢 Idle", classes="agent-item")
            self.agent_widgets[name] = w
            grid.mount(w)
            
        # Initialize Kanban Table
        table = self.query_one("#kanban-board")
        table.add_columns("Status", "Task")
        
        # Start background worker
        self.run_worker(self.update_loop, exclusive=True)
        
        self.log("System initialized. Ready.")

    async def update_loop(self):
        """Periodically fetch data and update UI."""
        while self.is_running:
            kanban, agents, metrics = self.data_source.update()
            self.update_agents(agents)
            self.update_kanban(kanban)
            self.update_metrics(metrics)
            await asyncio.sleep(2)

    def update_agents(self, statuses: Dict[str, str]):
        for name, status in statuses.items():
            if name in self.agent_widgets:
                self.agent_widgets[name].update_status(status)

    def update_kanban(self, tasks: Dict[str, List[str]]):
        table = self.query_one("#kanban-board")
        table.clear()
        for status, task_list in tasks.items():
            for task in task_list:
                status_icon = "📥" if status == "todo" else ("🔄" if status == "doing" else "✅")
                table.add_row(status_icon, task)

    def update_metrics(self, metrics: Dict[str, Any]):
        panel = self.query_one("#metrics-panel")
        cost_bar = "█" * int(metrics["cost"] * 2) + "░" * (25 - int(metrics["cost"] * 2))
        panel.renderable = (
            f"Input Tokens: {metrics['tokens_in']:,}\n"
            f"Output Tokens: {metrics['tokens_out']:,}\n"
            f"Cost: ${metrics['cost']:.2f} [red] {cost_bar}" if metrics['cost'] > 50 
            else f"Cost: ${metrics['cost']:.2f} [green] {cost_bar}"
        )

    def action_focus_input(self):
        self.query_one("#command-input").focus()

    def on_input_submitted(self, event: Input.Submitted):
        """Handle command input."""
        log = self.query_one("#log-viewer")
        cmd = event.value
        log.write(f"[bold green]$ {cmd}[/]")
        event.value = "" # Clear input
        
        # Simulate command processing
        if cmd.lower() == "scan":
            log.write("[yellow]Scanning dependencies... Found 0 vulnerabilities.[/]")
        elif cmd.lower() == "status":
            log.write("[cyan]All systems operational.[/]")
        else:
            log.write(f"[dim]Executing: {cmd}... Done.[/]")
