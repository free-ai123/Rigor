"""Tests for the constrained agent terminal."""

from rigor.modules.terminal import AgentTerminal


def test_terminal_blocks_shell_commands(tmp_path):
    term = AgentTerminal(workdir=str(tmp_path))

    allowed, reason = term.is_command_allowed("bash -lc 'echo unsafe'")

    assert allowed is False
    assert "not in allowed list" in reason


def test_terminal_blocks_python_inline_execution(tmp_path):
    term = AgentTerminal(workdir=str(tmp_path))

    allowed, reason = term.is_command_allowed("python -c 'print(1)'")

    assert allowed is False
    assert "blocked argument" in reason


def test_terminal_allows_pytest_command(tmp_path):
    term = AgentTerminal(workdir=str(tmp_path))

    allowed, reason = term.is_command_allowed("pytest -v --tb=short")

    assert allowed is True
    assert reason == "OK"
