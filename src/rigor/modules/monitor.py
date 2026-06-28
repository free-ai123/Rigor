"""Runtime status, dashboard, cost, and budget helpers for the Rigor CLI."""

from __future__ import annotations

import json
import os
import shutil
import sqlite3
import subprocess
import time
from contextlib import closing
from pathlib import Path

from rich.console import Console
from rich.table import Table

console = Console()

ROLES = [
    ("orchestrator", "orchestrator"),
    ("product-manager", "product-manager"),
    ("tech-lead", "tech-lead"),
    ("backend-engineer", "backend-engineer"),
    ("frontend-engineer", "frontend-engineer"),
    ("data-scientist", "data-scientist"),
    ("data-engineer", "data-engineer"),
    ("code-reviewer", "code-reviewer"),
    ("security-auditor", "security-auditor"),
    ("qa-engineer", "qa-engineer"),
    ("devops-engineer", "devops-engineer"),
    ("technical-writer", "technical-writer"),
]


def _hermes_home() -> Path:
    return Path(os.getenv("HERMES_HOME", "~/.hermes")).expanduser()


def _profiles_dir() -> Path:
    return _hermes_home() / "profiles"


def _log_dir() -> Path:
    return _hermes_home() / "logs"


def _budget_file() -> Path:
    return _hermes_home() / ".rigor_budget"


def _kanban_db_path() -> Path:
    candidates = [
        _hermes_home() / "kanban.db",
        _hermes_home() / "kanban" / "board.db",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


def _hermes_config_value(key: str) -> str:
    result = _run(["hermes", "config", "get", key])
    if result and result.returncode == 0 and _is_configured_value(result.stdout.strip()):
        return result.stdout.strip()

    config_path = _hermes_home() / "config.yaml"
    if not config_path.exists():
        return ""
    return _read_simple_yaml_value(config_path, key)


def _read_simple_yaml_value(path: Path, dotted_key: str) -> str:
    values: dict[str, str] = {}
    stack: list[tuple[int, str]] = []
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return ""

    for raw_line in lines:
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue
        if raw_line.lstrip().startswith("- "):
            continue
        indent = len(raw_line) - len(raw_line.lstrip(" "))
        stripped = raw_line.strip()
        if ":" not in stripped:
            continue
        key, value = stripped.split(":", 1)
        key = key.strip()
        value = value.strip()
        while stack and stack[-1][0] >= indent:
            stack.pop()
        current_path = ".".join([item[1] for item in stack] + [key])
        if value:
            values[current_path] = value.strip("'\"")
        else:
            stack.append((indent, key))
    return values.get(dotted_key, "")


def _is_configured_value(value: str | None) -> bool:
    normalized = (value or "").strip().lower()
    return normalized not in {"", "not set", "none", "null", "unknown"}


def _run(args: list[str], timeout: int = 5) -> subprocess.CompletedProcess[str] | None:
    if not args or shutil.which(args[0]) is None:
        return None
    try:
        return subprocess.run(args, capture_output=True, text=True, timeout=timeout)
    except Exception:
        return None


def _role_status(role: str) -> tuple[str, str, str]:
    profile_dir = _profiles_dir() / role
    if not profile_dir.exists():
        return "missing", "Never", "-"

    sessions_dir = profile_dir / "sessions"
    latest_session: Path | None = None
    if sessions_dir.exists():
        sessions = [p for p in sessions_dir.iterdir() if not p.name.startswith(".")]
        if sessions:
            latest_session = max(sessions, key=lambda p: p.stat().st_mtime)
            age = time.time() - latest_session.stat().st_mtime
            last_seen = time.strftime("%H:%M:%S", time.localtime(latest_session.stat().st_mtime))
            session_id = latest_session.name.split("_")[0][:12]
            if age < 60:
                return "active", last_seen, session_id
            if age < 300:
                return "idle", last_seen, session_id

    gateway_log = _log_dir() / "gateway.log"
    role_log = _log_dir() / f"{role}.log"
    for log_path in (gateway_log, role_log):
        if log_path.exists():
            try:
                tail = log_path.read_text(encoding="utf-8", errors="replace")[-4000:].lower()
            except OSError:
                continue
            if "error" in tail and role.lower() in tail:
                return "error", "recent", latest_session.name[:12] if latest_session else "-"

    if latest_session:
        last_seen = time.strftime("%H:%M:%S", time.localtime(latest_session.stat().st_mtime))
        return "ready", last_seen, latest_session.name.split("_")[0][:12]
    return "ready", "Never", "-"


def _classify_task_status(status: str) -> str:
    normalized = (status or "").lower()
    if normalized in {"done", "complete", "completed", "success", "passed"}:
        return "done"
    if normalized in {"doing", "in_progress", "running", "working", "active"}:
        return "running"
    if normalized in {"review", "blocked", "failed"}:
        return "review"
    return "todo"


def _kanban_summary() -> dict[str, int]:
    summary = {"total": 0, "todo": 0, "running": 0, "review": 0, "done": 0}
    db_path = _kanban_db_path()
    if db_path.exists():
        try:
            with closing(sqlite3.connect(db_path)) as conn:
                cur = conn.execute("SELECT status, COUNT(*) FROM tasks GROUP BY status")
                for status, count in cur.fetchall():
                    bucket = _classify_task_status(status)
                    summary[bucket] += int(count)
                    summary["total"] += int(count)
            return summary
        except sqlite3.Error:
            pass

    result = _run(["hermes", "kanban", "list", "--no-color"], timeout=10)
    if not result or not result.stdout.strip():
        return summary

    for line in result.stdout.splitlines():
        summary["total"] += 1
        bucket = _classify_task_status(line)
        summary[bucket] += 1
    return summary


def _token_usage() -> tuple[int, int]:
    result = _run(["hermes", "insights", "--days", "1", "--json"], timeout=10)
    if result and result.stdout.strip():
        try:
            data = json.loads(result.stdout)
            return int(data.get("total_input_tokens", 0)), int(data.get("total_output_tokens", 0))
        except (TypeError, ValueError, json.JSONDecodeError):
            pass

    total_bytes = 0
    logs = _log_dir()
    if logs.exists():
        cutoff = time.time() - 24 * 60 * 60
        checked = 0
        for item in logs.rglob("*"):
            if checked >= 1000:
                break
            if not item.is_file():
                continue
            checked += 1
            try:
                stat = item.stat()
            except OSError:
                continue
            if stat.st_mtime >= cutoff:
                total_bytes += stat.st_size
    return 0, total_bytes // 4


def _cost_estimate(input_tokens: int, output_tokens: int) -> tuple[float, float, float]:
    input_cost = input_tokens * 3 / 1_000_000
    output_cost = output_tokens * 15 / 1_000_000
    return input_cost, output_cost, input_cost + output_cost


def _get_budget() -> float:
    path = _budget_file()
    if not path.exists():
        return 0.0
    try:
        return float(path.read_text(encoding="utf-8").strip() or 0)
    except (OSError, ValueError):
        return 0.0


def _set_budget(amount: float) -> None:
    path = _budget_file()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"{amount:.2f}", encoding="utf-8")


def _build_status_table() -> Table:
    table = Table(title="Rigor Agent Team")
    table.add_column("Role", style="cyan")
    table.add_column("Status")
    table.add_column("Last Seen")
    table.add_column("Session")
    for role, label in ROLES:
        status, last_seen, session = _role_status(role)
        style = {"active": "green", "idle": "blue", "error": "red", "missing": "yellow"}.get(status, "white")
        table.add_row(label, f"[{style}]{status}[/]", last_seen, session)
    return table


def run_status() -> None:
    """Print a one-shot system health snapshot."""
    console.print("[bold]Rigor System Status[/]")
    hermes = _run(["hermes", "--version"])
    console.print(f"  Hermes: {hermes.stdout.strip() if hermes and hermes.stdout.strip() else '[red]Not installed[/]'}")

    model = _hermes_config_value("model.default")
    console.print(f"  Model:  {model if _is_configured_value(model) else 'Not set'}")

    counts = {"active": 0, "idle": 0, "issues": 0}
    for role, _ in ROLES:
        status, _, _ = _role_status(role)
        if status == "active":
            counts["active"] += 1
        elif status in {"idle", "ready"}:
            counts["idle"] += 1
        else:
            counts["issues"] += 1
    console.print(
        f"  Agents: [green]{counts['active']} active[/] | "
        f"[blue]{counts['idle']} idle[/] | [red]{counts['issues']} issues[/]"
    )

    kanban = _kanban_summary()
    console.print(
        f"  Kanban: {kanban['total']} tasks ({kanban['todo']} todo, {kanban['running']} running, {kanban['done']} done)"
    )

    input_tokens, output_tokens = _token_usage()
    _, _, total = _cost_estimate(input_tokens, output_tokens)
    console.print(f"  Cost:   ${total:.4f} estimated")


def run_cost_report() -> None:
    """Print token and estimated cost information."""
    input_tokens, output_tokens = _token_usage()
    input_cost, output_cost, total = _cost_estimate(input_tokens, output_tokens)

    table = Table(title="Rigor Cost Report")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", justify="right")
    table.add_row("Input tokens", f"{input_tokens:,}")
    table.add_row("Output tokens", f"{output_tokens:,}")
    table.add_row("Input cost", f"${input_cost:.4f}")
    table.add_row("Output cost", f"${output_cost:.4f}")
    table.add_row("Total cost", f"${total:.4f}")
    console.print(table)

    activity = Table(title="Per-Role Activity")
    activity.add_column("Role", style="cyan")
    activity.add_column("Status")
    activity.add_column("Sessions", justify="right")
    for role, label in ROLES:
        sessions_dir = _profiles_dir() / role / "sessions"
        sessions = len(list(sessions_dir.iterdir())) if sessions_dir.exists() else 0
        status, _, _ = _role_status(role)
        activity.add_row(label, status, str(sessions))
    console.print(activity)


def manage_budget(amount: str | None) -> None:
    """Set or display the current budget."""
    if not amount:
        current = _get_budget()
        if current <= 0:
            console.print("[yellow]No budget set. Use: rigor budget <amount>[/]")
        else:
            console.print(f"[green]Current budget: ${current:.2f}[/]")
        return

    try:
        value = float(amount)
    except ValueError:
        console.print(f"[red]Invalid budget amount: {amount}[/]")
        return
    if value < 0:
        console.print("[red]Budget must be non-negative[/]")
        return

    _set_budget(value)
    console.print(f"[green]Budget set to ${value:.2f}[/]")


def run_dashboard() -> None:
    """Run a simple auto-refreshing terminal dashboard."""
    try:
        while True:
            console.clear()
            run_status()
            console.print()
            console.print(_build_status_table())
            console.print("[dim]Refreshes every 3s. Press Ctrl+C to exit.[/]")
            time.sleep(3)
    except KeyboardInterrupt:
        console.print("\n[yellow]Monitor stopped[/]")
