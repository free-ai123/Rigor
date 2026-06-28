"""Tests for TUI command parsing helpers."""

import sys

from rigor.tui.app import build_tui_command
from rigor.tui.connector import resolve_kanban_db_path


def test_tui_command_accepts_rigor_prefix():
    argv, message = build_tui_command("rigor scan --language python")

    assert message is None
    assert argv == [sys.executable, "-m", "rigor.cli", "scan", "--language", "python"]


def test_tui_command_accepts_rigor_command_without_prefix():
    argv, message = build_tui_command("status")

    assert message is None
    assert argv == [sys.executable, "-m", "rigor.cli", "status"]


def test_tui_command_accepts_case_insensitive_rigor_command():
    argv, message = build_tui_command("Scan --language python")

    assert message is None
    assert argv == [sys.executable, "-m", "rigor.cli", "scan", "--language", "python"]


def test_tui_command_accepts_case_insensitive_rigor_prefix_args():
    argv, message = build_tui_command("rigor Scan --language python")

    assert message is None
    assert argv == [sys.executable, "-m", "rigor.cli", "scan", "--language", "python"]


def test_tui_command_accepts_chinese_alias():
    argv, message = build_tui_command("扫描 --language python")

    assert message is None
    assert argv == [sys.executable, "-m", "rigor.cli", "scan", "--language", "python"]


def test_tui_command_accepts_chinese_alias_after_rigor_prefix():
    argv, message = build_tui_command("rigor 状态")

    assert message is None
    assert argv == [sys.executable, "-m", "rigor.cli", "status"]


def test_tui_command_accepts_chinese_help():
    argv, message = build_tui_command("帮助")

    assert argv is None
    assert "状态" in message


def test_tui_command_accepts_chinese_kanban_alias():
    argv, message = build_tui_command("看板")

    assert message is None
    assert argv == ["hermes", "kanban", "list"]


def test_tui_command_accepts_english_kanban_alias():
    argv, message = build_tui_command("kanban")

    assert message is None
    assert argv == ["hermes", "kanban", "list"]


def test_tui_command_accepts_gateway_alias():
    argv, message = build_tui_command("gateway")

    assert message is None
    assert argv == ["hermes", "gateway", "status"]


def test_tui_command_accepts_logs_alias_case_insensitive():
    argv, message = build_tui_command("Logs")

    assert message is None
    assert argv == ["hermes", "logs"]


def test_tui_command_routes_plain_text_to_chat():
    argv, message = build_tui_command("hello")

    assert message is None
    assert argv == ["hermes", "chat", "-q", "hello", "-Q", "--max-turns", "4"]


def test_tui_command_routes_chinese_plain_text_to_chat():
    argv, message = build_tui_command("你好")

    assert message is None
    assert argv == ["hermes", "chat", "-q", "你好", "-Q", "--max-turns", "4"]


def test_tui_command_resumes_chat_session():
    argv, message = build_tui_command("hello again", chat_session_id="session-123")

    assert message is None
    assert argv == [
        "hermes",
        "chat",
        "-q",
        "hello again",
        "-Q",
        "--max-turns",
        "4",
        "--resume",
        "session-123",
    ]


def test_tui_command_accepts_explicit_chinese_chat_prefix():
    argv, message = build_tui_command("对话 帮我看一下项目状态")

    assert message is None
    assert argv == ["hermes", "chat", "-q", "帮我看一下项目状态", "-Q", "--max-turns", "4"]


def test_tui_command_allows_read_only_hermes_commands():
    argv, message = build_tui_command("hermes kanban list")

    assert message is None
    assert argv == ["hermes", "kanban", "list"]


def test_tui_command_blocks_mutating_hermes_commands():
    argv, message = build_tui_command("hermes kanban create demo")

    assert argv is None
    assert "read-only Hermes commands" in message


def test_tui_command_blocks_following_logs():
    argv, message = build_tui_command("hermes logs -f")

    assert argv is None
    assert "read-only Hermes commands" in message


def test_resolve_kanban_db_path_prefers_current_hermes_location(tmp_path):
    current = tmp_path / "kanban.db"
    current.write_text("", encoding="utf-8")
    legacy_dir = tmp_path / "kanban"
    legacy_dir.mkdir()
    (legacy_dir / "board.db").write_text("", encoding="utf-8")

    assert resolve_kanban_db_path(tmp_path) == current
