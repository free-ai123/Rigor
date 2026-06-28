"""
Rigor TUI v2.1 - Interactive k9s-style dashboard for Rigor AI Engineering Team.

Features:
- Real-time data from Hermes Kanban DB
- Multi-view switching (Monitor, Logs, Settings)
- Interactive Kanban board (select, view details)
- Agent status matrix with live updates
- Token/Cost monitoring
"""

import asyncio
import re
import shlex
import shutil
import sys
from typing import Any

from rich.text import Text
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Grid, Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import DataTable, Footer, Header, Input, Label, RichLog, Static

from .connector import RigorDataConnector

# Constants
AGENT_ICONS = {
    "orchestrator": "🎯",
    "product-manager": "📋",
    "tech-lead": "🏗️",
    "backend-engineer": "⚙️",
    "frontend-engineer": "🎨",
    "data-scientist": "📊",
    "data-engineer": "🔧",
    "code-reviewer": "🔍",
    "qa-engineer": "✅",
    "security-auditor": "🛡️",
    "devops-engineer": "🚀",
    "technical-writer": "📝",
}
COMMAND_TIMEOUT_SECONDS = 120
CHAT_TIMEOUT_SECONDS = 240
RIGOR_COMMANDS = {
    "budget",
    "code-map",
    "cost",
    "init",
    "install",
    "knowledge",
    "mock",
    "monitor",
    "pr",
    "report",
    "scan",
    "setup",
    "status",
    "watch-fix",
    "webhook",
}
CHAT_COMMANDS = {"ask", "chat", "talk", "问", "对话", "聊天"}
CHINESE_COMMAND_ALIASES = {
    "？": "help",
    "帮助": "help",
    "清屏": "clear",
    "状态": "status",
    "系统状态": "status",
    "扫描": "scan",
    "安全扫描": "scan",
    "代码地图": "code-map",
    "代码结构": "code-map",
    "成本": "cost",
    "费用": "cost",
    "预算": "budget",
    "看板": "hermes kanban list",
    "任务": "hermes kanban list",
    "日志": "hermes logs",
    "日志列表": "hermes logs list",
    "网关状态": "hermes gateway status",
    "诊断": "hermes doctor",
}
COMMAND_ALIASES = {
    **CHINESE_COMMAND_ALIASES,
    "kanban": "hermes kanban list",
    "log": "hermes logs",
    "logs": "hermes logs",
    "tasks": "hermes kanban list",
    "task": "hermes kanban list",
    "gateway": "hermes gateway status",
    "doctor": "hermes doctor",
    "cls": "clear",
}
HERMES_SAFE_PREFIXES = {
    ("hermes", "--version"),
    ("hermes", "config", "get"),
    ("hermes", "doctor"),
    ("hermes", "gateway", "status"),
    ("hermes", "kanban", "list"),
    ("hermes", "kanban", "show"),
    ("hermes", "logs"),
}
CHAT_SESSION_PATTERN = re.compile(r"^\s*session_id:\s*(?P<session_id>\S+)\s*$", re.MULTILINE)


def build_tui_command(raw_command: str, chat_session_id: str | None = None) -> tuple[list[str] | None, str | None]:
    """Convert TUI input into a safe argv list or a user-facing message."""
    original_command = raw_command.strip()
    raw_command = _normalize_command_alias(original_command)
    try:
        parts = shlex.split(raw_command)
    except ValueError as exc:
        return None, f"Could not parse command: {exc}"

    if not parts:
        return None, None

    command = parts[0]
    command_key = command.casefold()
    if command_key in {"help", "?"}:
        return None, (
            "可以直接提问聊天，也可以运行命令。"
            "命令示例：状态, 扫描, 代码地图 --dir ., 成本, 看板, 日志, 清屏；"
            "English: status, scan, code-map --dir ., kanban, logs, gateway, doctor. "
            "Use 对话/ask/chat + text to force chat mode."
        )

    if command_key == "clear":
        return None, "__CLEAR__"

    if command_key in CHAT_COMMANDS:
        prompt = raw_command[len(command) :].strip()
        if not prompt:
            return None, "请输入要对话的内容，例如：对话 帮我分析当前项目状态"
        return _build_chat_argv(prompt, chat_session_id), None

    if command_key == "rigor":
        args = _normalize_rigor_args(parts[1:])
        if not args:
            return [sys.executable, "-m", "rigor.cli", "--help"], None
    elif command_key in RIGOR_COMMANDS:
        args = [command_key, *parts[1:]]
    elif command_key == "hermes":
        parts = [command_key, *parts[1:]]
        if _is_safe_hermes_command(parts):
            return parts, None
        return None, "Only read-only Hermes commands are allowed here, such as: hermes kanban list"
    else:
        return _build_chat_argv(original_command, chat_session_id), None

    if args[0] == "tui":
        return None, "You are already inside the TUI."
    return [sys.executable, "-m", "rigor.cli", *args], None


def _is_safe_hermes_command(parts: list[str]) -> bool:
    normalized = [part.casefold() if index < 3 else part for index, part in enumerate(parts)]
    if normalized[:2] == ["hermes", "logs"] and any(part in {"-f", "--follow"} for part in normalized[2:]):
        return False
    return any(tuple(normalized[: len(prefix)]) == prefix for prefix in HERMES_SAFE_PREFIXES)


def _normalize_command_alias(raw_command: str) -> str:
    lookup = raw_command.casefold()
    alias_map = {alias.casefold(): canonical for alias, canonical in COMMAND_ALIASES.items()}
    if lookup in alias_map:
        return alias_map[lookup]
    for alias, canonical in sorted(COMMAND_ALIASES.items(), key=lambda item: len(item[0]), reverse=True):
        prefix = f"{alias.casefold()} "
        if lookup.startswith(prefix):
            return f"{canonical} {raw_command[len(alias) + 1 :]}"
    return raw_command


def _normalize_rigor_args(args: list[str]) -> list[str]:
    if not args:
        return args
    normalized = _normalize_command_alias(" ".join(args))
    try:
        parts = shlex.split(normalized)
    except ValueError:
        return args
    if parts and parts[0].casefold() in RIGOR_COMMANDS:
        return [parts[0].casefold(), *parts[1:]]
    return parts


def _build_chat_argv(prompt: str, chat_session_id: str | None = None) -> list[str]:
    argv = ["hermes", "chat", "-q", prompt, "-Q", "--max-turns", "4"]
    if chat_session_id:
        argv.extend(["--resume", chat_session_id])
    return argv


def _is_chat_argv(argv: list[str]) -> bool:
    normalized = [part.casefold() for part in argv[:2]]
    return normalized == ["hermes", "chat"] and "-q" in argv


class MonitorScreen(Screen):
    """Main monitoring dashboard screen."""

    BINDINGS = [
        Binding("q", "app.quit", "Quit"),
        Binding("l", "focus_input", "Input"),
        Binding("1", "show_monitor", "Monitor"),
        Binding("2", "show_logs", "Logs"),
        Binding("3", "show_settings", "Settings"),
        Binding("f5", "run_status", "Status"),
        Binding("f6", "run_kanban", "Kanban"),
        Binding("f7", "run_scan", "Scan"),
        Binding("f8", "paste_clipboard", "Paste"),
    ]

    def __init__(self, connector: RigorDataConnector):
        super().__init__()
        self.connector = connector
        self.agent_widgets = {}
        self.chat_session_id: str | None = None

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Horizontal(id="main-layout"):
            # Left: Input & Log
            with Vertical(id="left-panel"):
                yield Label("📝 Command Input / 中文命令", classes="panel-title")
                yield Input(placeholder="输入命令或直接提问... 如：帮助、状态、扫描、看板、你好", id="cmd-input")
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
        self.log_info(
            "System initialized. Type help/帮助 for commands, or type any question to chat. F8 pastes clipboard text."
        )
        self.action_focus_input()

    async def update_loop(self):
        """Periodically update UI from data source."""
        while True:
            agents = self.connector.get_agent_status()
            self.update_agents(agents)

            tasks = self.connector.get_kanban_tasks()
            self.update_kanban(tasks)

            metrics = self.connector.get_metrics()
            self.update_metrics(metrics)

            await asyncio.sleep(2)

    def update_agents(self, statuses: dict[str, str]):
        for name, status in statuses.items():
            if name in self.agent_widgets:
                self.agent_widgets[name].update(status)

    def update_kanban(self, tasks: dict[str, list[dict]]):
        table = self.query_one("#kanban-table")
        table.clear()
        rows = 0
        for status, task_list in tasks.items():
            for task in task_list:
                tid = str(task.get("id", "?"))[:6]
                title = task.get("title", "Untitled")[:20]
                assignee = task.get("assignee", "Unassigned")
                icon = "📥" if status == "todo" else ("🔄" if status == "doing" else "✅")
                table.add_row(tid, f"{icon} {status}", title, assignee)
                rows += 1
        if rows == 0:
            table.add_row("-", "-", "No Kanban tasks found", "-")

    def update_metrics(self, metrics: dict[str, Any]):
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
        cmd = event.value.strip()
        if not cmd:
            return
        event.input.value = ""
        self.submit_command(cmd)

    def submit_command(self, cmd: str):
        log = self.query_one("#log-viewer")
        log.write(f"[bold green]$ {cmd}[/]")
        argv, message = build_tui_command(cmd, self.chat_session_id)
        if message == "__CLEAR__":
            log.clear()
            return
        if message:
            log.write(f"[yellow]{message}[/]")
            return
        if not argv:
            return

        self.run_worker(self.execute_command(argv), name=f"cmd:{cmd}", exclusive=False)

    def action_run_status(self):
        self.submit_command("status")

    def action_run_kanban(self):
        self.submit_command("kanban")

    def action_run_scan(self):
        self.submit_command("scan")

    def action_paste_clipboard(self):
        self.run_worker(self.paste_clipboard_command(), name="clipboard", exclusive=False)

    async def paste_clipboard_command(self):
        log = self.query_one("#log-viewer")
        if shutil.which("pbpaste") is None:
            log.write("[yellow]Clipboard paste requires macOS pbpaste. Type an English command or use F5/F6/F7.[/]")
            return
        try:
            proc = await asyncio.create_subprocess_exec(
                "pbpaste",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=3)
        except Exception as exc:
            log.write(f"[yellow]Could not read clipboard: {exc}[/]")
            return

        text = stdout.decode("utf-8", errors="replace").strip()
        command = next((line.strip() for line in text.splitlines() if line.strip()), "")
        if not command:
            log.write("[yellow]Clipboard is empty.[/]")
            return

        input_widget = self.query_one("#cmd-input", Input)
        input_widget.value = command
        self.submit_command(command)

    async def execute_command(self, argv: list[str]):
        log = self.query_one("#log-viewer")
        log.write("[dim]Running...[/]")
        timeout = CHAT_TIMEOUT_SECONDS if _is_chat_argv(argv) else COMMAND_TIMEOUT_SECONDS
        try:
            proc = await asyncio.create_subprocess_exec(
                *argv,
                cwd=str(self.connector.workspace),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        except TimeoutError:
            log.write(f"[red]Command timed out after {timeout}s.[/]")
            return
        except FileNotFoundError:
            log.write(f"[red]Command not found: {argv[0]}[/]")
            return
        except Exception as exc:
            log.write(f"[red]Command failed: {exc}[/]")
            return

        if _is_chat_argv(argv):
            stderr = self._capture_chat_session(stderr)

        self._write_command_output(stdout)
        self._write_command_output(stderr)
        if proc.returncode == 0:
            log.write("[green]Done.[/]")
        else:
            log.write(f"[red]Exited with code {proc.returncode}.[/]")

        agents = self.connector.get_agent_status()
        self.update_agents(agents)
        self.update_kanban(self.connector.get_kanban_tasks())
        self.update_metrics(self.connector.get_metrics())

    def _write_command_output(self, output: bytes):
        if not output:
            return
        log = self.query_one("#log-viewer")
        text = output.decode("utf-8", errors="replace").strip()
        if not text:
            return
        for line in text.splitlines()[:300]:
            log.write(Text.from_ansi(line))

    def _capture_chat_session(self, stderr: bytes) -> bytes:
        if not stderr:
            return stderr
        text = stderr.decode("utf-8", errors="replace")
        match = CHAT_SESSION_PATTERN.search(text)
        if match:
            self.chat_session_id = match.group("session_id")
            text = CHAT_SESSION_PATTERN.sub("", text)
        return text.strip().encode("utf-8")

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
        super().update(f"{AGENT_ICONS.get(self.agent_name, '❓')} {self.agent_name}: {status}")
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
