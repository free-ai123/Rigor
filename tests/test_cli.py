"""Tests for the Rigor CLI entry point."""

import os
import subprocess

from click.testing import CliRunner
from rigor import cli as cli_module
from rigor.cli import build_hermes_chat_command, build_init_project_command, main, sync_hermes_profile_runtime


def test_cli_help_lists_core_commands():
    runner = CliRunner()
    result = runner.invoke(main, ["--help"])

    assert result.exit_code == 0
    assert "watch-fix" in result.output
    assert "status" in result.output
    assert "chat" in result.output
    assert "frame" in result.output


def test_build_hermes_chat_command_defaults_to_orchestrator_profile():
    argv = build_hermes_chat_command()

    assert argv == ["hermes", "--profile", "orchestrator", "chat", "--cli"]


def test_build_hermes_chat_command_can_force_profile():
    argv = build_hermes_chat_command(profile="backend-engineer")

    assert argv == ["hermes", "--profile", "backend-engineer", "chat", "--cli"]


def test_build_hermes_chat_command_can_reuse_current_config_without_profile():
    argv = build_hermes_chat_command(profile=None)

    assert argv == ["hermes", "chat", "--cli"]


def test_build_hermes_chat_command_supports_query_and_resume():
    argv = build_hermes_chat_command(query="hello", resume="session-123", max_turns=2)

    assert argv == [
        "hermes",
        "--profile",
        "orchestrator",
        "chat",
        "--cli",
        "--query",
        "hello",
        "--resume",
        "session-123",
        "--max-turns",
        "2",
    ]


def test_chat_command_execs_orchestrator_chat(monkeypatch):
    captured = {}
    monkeypatch.setattr(cli_module, "_exec_hermes_chat", lambda argv: captured.setdefault("argv", argv))
    monkeypatch.setattr(
        cli_module, "sync_hermes_profile_runtime", lambda profile: captured.setdefault("profile", profile)
    )

    runner = CliRunner()
    result = runner.invoke(main, ["chat", "帮我分析项目", "--max-turns", "2"])

    assert result.exit_code == 0
    assert captured["argv"] == [
        "hermes",
        "--profile",
        "orchestrator",
        "chat",
        "--cli",
        "--query",
        "帮我分析项目",
        "--max-turns",
        "2",
    ]
    assert captured["profile"] == "orchestrator"


def test_chat_command_can_skip_profile_sync(monkeypatch):
    captured = {}
    monkeypatch.setattr(cli_module, "_exec_hermes_chat", lambda argv: captured.setdefault("argv", argv))
    monkeypatch.setattr(
        cli_module,
        "sync_hermes_profile_runtime",
        lambda profile: captured.setdefault("profile", profile),
    )

    runner = CliRunner()
    result = runner.invoke(main, ["chat", "--no-sync-profile"])

    assert result.exit_code == 0
    assert captured["argv"] == ["hermes", "--profile", "orchestrator", "chat", "--cli"]
    assert "profile" not in captured


def test_build_init_project_command_defaults_to_script_default():
    argv = build_init_project_command("my api")

    assert argv == ["bash", str(cli_module.PROJECT_ROOT / "scripts" / "init-project.sh"), "my api"]


def test_build_init_project_command_supports_target_dir():
    argv = build_init_project_command("my api", target_dir="~/projects/my-api")

    assert argv == [
        "bash",
        str(cli_module.PROJECT_ROOT / "scripts" / "init-project.sh"),
        "my api",
        "--dir",
        "~/projects/my-api",
    ]


def test_init_project_script_scaffolds_outside_repo_workspace(tmp_path):
    target = tmp_path / "projects" / "中文-api"
    script = cli_module.PROJECT_ROOT / "scripts" / "init-project.sh"

    result = subprocess.run(
        ["bash", str(script), "中文 API", "--dir", str(target)],
        capture_output=True,
        text=True,
        timeout=15,
    )

    assert result.returncode == 0, result.stderr
    assert (target / "README.md").exists()
    assert (target / "artifacts" / "orchestrator" / "problem-frame.md").exists()
    assert (target / "artifacts" / "product-manager" / "prd.md").exists()
    assert "workspace/" not in (target / "README.md").read_text(encoding="utf-8")


def test_init_project_script_defaults_to_projects_root(tmp_path):
    projects_root = tmp_path / "projects"
    target = projects_root / "中文-api"
    script = cli_module.PROJECT_ROOT / "scripts" / "init-project.sh"
    env = {**os.environ, "RIGOR_PROJECTS_DIR": str(projects_root)}

    result = subprocess.run(
        ["bash", str(script), "中文 API"],
        capture_output=True,
        text=True,
        timeout=15,
        env=env,
    )

    assert result.returncode == 0, result.stderr
    assert (target / "README.md").exists()
    assert (target / "artifacts" / "orchestrator" / "problem-frame.json").exists()
    assert str(target) in result.stdout


def test_frame_command_saves_problem_frame_artifacts(tmp_path):
    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "frame",
            "帮我做一个 AI Agent 方案",
            "--dir",
            str(tmp_path),
            "--fail-on-clarify",
        ],
    )

    assert result.exit_code != 0
    assert "requires clarification" in result.output
    assert (tmp_path / "artifacts" / "orchestrator" / "problem-frame.md").exists()
    assert (tmp_path / "artifacts" / "orchestrator" / "problem-frame.json").exists()


def test_frame_command_can_confirm_problem_frame(tmp_path):
    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "frame",
            "为产品团队写一份正式报告，分析中国市场，包含价格、功能和成功建议",
            "--dir",
            str(tmp_path),
            "--confirm",
        ],
        input="y\n",
    )

    assert result.exit_code == 0
    frame_json = tmp_path / "artifacts" / "orchestrator" / "problem-frame.json"
    assert '"confirmed_by_user": true' in frame_json.read_text(encoding="utf-8")


def test_frame_command_rejects_unconfirmed_problem_frame(tmp_path):
    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "frame",
            "为产品团队写一份正式报告，分析中国市场，包含价格、功能和成功建议",
            "--dir",
            str(tmp_path),
            "--confirm",
        ],
        input="n\n需要调整目标用户\n",
    )

    assert result.exit_code != 0
    assert "was not confirmed" in result.output
    frame_json = tmp_path / "artifacts" / "orchestrator" / "problem-frame.json"
    assert '"confirmation_status": "rejected"' in frame_json.read_text(encoding="utf-8")


def test_tui_command_is_deprecated_chat_alias(monkeypatch):
    captured = {}
    monkeypatch.setattr(cli_module, "_exec_hermes_chat", lambda argv: captured.setdefault("argv", argv))
    monkeypatch.setattr(
        cli_module, "sync_hermes_profile_runtime", lambda profile: captured.setdefault("profile", profile)
    )

    runner = CliRunner()
    result = runner.invoke(main, ["tui"])

    assert result.exit_code == 0
    assert "deprecated" in result.output
    assert captured["argv"] == ["hermes", "--profile", "orchestrator", "chat", "--cli"]
    assert captured["profile"] == "orchestrator"


def test_sync_hermes_profile_runtime_copies_root_config_and_auth(tmp_path):
    hermes_home = tmp_path / ".hermes"
    hermes_home.mkdir()
    (hermes_home / "config.yaml").write_text("model:\n  provider: alibaba\n", encoding="utf-8")
    (hermes_home / ".env").write_text("DASHSCOPE_API_KEY=test\n", encoding="utf-8")
    (hermes_home / "auth.json").write_text('{"provider":"alibaba"}\n', encoding="utf-8")

    sync_hermes_profile_runtime("orchestrator", hermes_home=hermes_home)

    profile_dir = hermes_home / "profiles" / "orchestrator"
    assert (profile_dir / "SOUL.md").exists()
    assert "provider: alibaba" in (profile_dir / "config.yaml").read_text(encoding="utf-8")
    assert "DASHSCOPE_API_KEY=test" in (profile_dir / ".env").read_text(encoding="utf-8")
    assert "alibaba" in (profile_dir / "auth.json").read_text(encoding="utf-8")


def test_status_command_runs_without_hermes(tmp_path, monkeypatch):
    monkeypatch.setenv("HERMES_HOME", str(tmp_path / ".hermes"))
    runner = CliRunner()
    result = runner.invoke(main, ["status"])

    assert result.exit_code == 0
    assert "Rigor System Status" in result.output
    assert "Hermes:" in result.output
    assert "Kanban:" in result.output
