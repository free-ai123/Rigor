"""Rigor CLI v2.0 — 统一入口"""

import json
import os
import shutil
import sys
from pathlib import Path
from typing import Any

import click
from rich.console import Console
from rich.markdown import Markdown

console = Console()
CHAT_CONTEXT_SETTINGS = {"ignore_unknown_options": True, "allow_extra_args": True}


def _find_project_root() -> Path:
    """Find the source checkout root when running from an editable install."""
    package_file = Path(__file__).resolve()
    candidates = [package_file.parents[2], Path.cwd()]
    for candidate in candidates:
        if (candidate / "scripts").is_dir():
            return candidate
    return package_file.parents[1]


PROJECT_ROOT = _find_project_root()
SOURCE_ROOT = Path(__file__).resolve().parents[1]
if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))


def build_hermes_chat_command(
    *,
    profile: str | None = "orchestrator",
    query: str | None = None,
    resume: str | None = None,
    continue_last: bool = False,
    model: str | None = None,
    provider: str | None = None,
    toolsets: str | None = None,
    max_turns: int | None = None,
    hermes_tui: bool = False,
    accept_hooks: bool = False,
    extra_args: list[str] | None = None,
) -> list[str]:
    """Build a Hermes chat command without invoking a shell."""
    argv = ["hermes"]
    if profile:
        argv.extend(["--profile", profile])
    argv.extend(["chat", "--tui" if hermes_tui else "--cli"])
    if query:
        argv.extend(["--query", query])
    if resume:
        argv.extend(["--resume", resume])
    elif continue_last:
        argv.append("--continue")
    if model:
        argv.extend(["--model", model])
    if provider:
        argv.extend(["--provider", provider])
    if toolsets:
        argv.extend(["--toolsets", toolsets])
    if max_turns is not None:
        argv.extend(["--max-turns", str(max_turns)])
    if accept_hooks:
        argv.append("--accept-hooks")
    if extra_args:
        argv.extend(extra_args)
    return argv


def _default_hermes_home() -> Path:
    configured = os.environ.get("HERMES_HOME", "").strip()
    if configured:
        candidate = Path(configured).expanduser()
        if candidate.parent.name == "profiles":
            return candidate.parent.parent
        return candidate
    return Path.home() / ".hermes"


def sync_hermes_profile_runtime(profile: str, hermes_home: Path | None = None) -> None:
    """Hydrate a Rigor profile with the user's current Hermes runtime config."""
    root = (hermes_home or _default_hermes_home()).expanduser()
    profile_dir = root / "profiles" / profile
    profile_dir.mkdir(parents=True, exist_ok=True)

    soul_src = PROJECT_ROOT / "profiles" / profile / "SOUL.md"
    if soul_src.exists():
        shutil.copy2(soul_src, profile_dir / "SOUL.md")

    fallback_config = PROJECT_ROOT / "profiles" / profile / "config.yaml"
    root_config = root / "config.yaml"
    if root_config.exists():
        shutil.copy2(root_config, profile_dir / "config.yaml")
    elif fallback_config.exists():
        shutil.copy2(fallback_config, profile_dir / "config.yaml")

    for name in (".env", "auth.json"):
        src = root / name
        if src.exists():
            dest = profile_dir / name
            shutil.copy2(src, dest)
            try:
                dest.chmod(0o600)
            except OSError:
                pass


def _exec_hermes_chat(argv: list[str]) -> None:
    if shutil.which("hermes") is None:
        raise click.ClickException("Hermes CLI not found. Run: bash scripts/bootstrap.sh")
    os.execvp(argv[0], argv)


@click.group()
@click.version_option(version="2.0.0", prog_name="rigor")
def main():
    """🤖 Rigor CLI v2.0 — 12-Role AI Engineering Team"""
    pass


# ===================== 安装/状态 =====================


@main.command()
@click.option("--platform", type=click.Choice(["github", "gitlab"]), default=None, help="Git 平台")
def install(platform):
    """安装 Rigor 专家团队（调用 shell 脚本）"""
    script = PROJECT_ROOT / "scripts" / "setup-expert-team.sh"
    if not script.exists():
        console.print("[red]❌ 找不到安装脚本[/]")
        return
    console.print("[cyan]正在启动智能安装向导...[/]")
    os.execv("bash", ["bash", str(script)])


@main.command()
def status():
    """系统健康状态"""
    from rigor.modules.monitor import run_status

    run_status()


# ===================== 监控 =====================


@main.command()
def monitor():
    """实时监控面板（文本模式）"""
    try:
        from rigor.modules.monitor import run_dashboard

        run_dashboard()
    except KeyboardInterrupt:
        console.print("\n[yellow]监控已退出[/]")


@main.command(name="cost")
def cost():
    """成本报告"""
    from rigor.modules.monitor import run_cost_report

    run_cost_report()


@main.command()
@click.argument("amount", required=False)
def budget(amount):
    """设置/查看预算"""
    from rigor.modules.monitor import manage_budget

    manage_budget(amount)


# ===================== PR 管理 (P0-1) =====================


@main.group()
def pr():
    """PR 自动生成 + Review"""
    pass


@pr.command("create")
@click.option("--repo", "-r", default=None, help="仓库 URL 或 owner/repo")
@click.option("--branch", "-b", default=None, help="源分支 (默认: 当前分支)")
@click.option("--base", default="main", help="目标分支 (默认: main)")
@click.option("--token", "-t", default=None, help="API Token")
@click.option("--platform", type=click.Choice(["github", "gitlab"]), default=None, help="平台类型")
@click.option("--no-review", is_flag=True, help="不添加自动 Review")
def pr_create(repo, branch, base, token, platform, no_review):
    """自动创建 PR 并添加 AI Review"""
    from rigor.modules.pr import create_pr

    result = create_pr(
        repo_url=repo,
        branch=branch,
        base=base,
        token=token,
        platform_type=platform,
        auto_review=not no_review,
    )
    if result["status"] == "created":
        console.print(f"\n[green]✅ PR #{result['pr_number']} 已创建![/]")
        console.print(f"  URL: {result['pr_url']}")
        if result.get("review_added"):
            console.print("  🤖 自动 Review: 已添加")
    elif result["status"] == "skipped":
        console.print(f"[yellow]⏭️  跳过: {result.get('reason')}[/]")
    else:
        console.print(f"[red]❌ 失败: {result.get('error')}[/]")


@pr.command("review")
@click.option("--repo", "-r", required=True, help="仓库 owner/repo")
@click.option("--pr", "-p", required=True, type=int, help="PR 编号")
@click.option("--token", "-t", default=None, help="API Token")
@click.option("--platform", type=click.Choice(["github", "gitlab"]), default=None)
def pr_review(repo, pr, token, platform):
    """对已有 PR 添加 AI Review"""
    from rigor.git.factory import create_platform
    from rigor.modules.pr import _generate_review

    platform_client = create_platform(platform_type=platform, token=token)

    # 获取 PR 信息
    pr_data = platform_client.get_pr(repo, pr)
    source = pr_data.get("head", {}).get("ref", "unknown")

    review = _generate_review(platform_client, repo, pr, source, "main")
    platform_client.add_pr_review(repo, pr, review, "COMMENT")

    console.print(f"[green]✅ Review 评论已添加到 #{pr}[/]")


# ===================== 安全扫描 (P0-2) =====================


@main.command(name="scan")
@click.option("--dir", "-d", default=".", help="项目目录")
@click.option("--language", type=click.Choice(["python", "nodejs", "all"]), default="all")
def scan(dir, language):
    """依赖安全扫描"""
    from rigor.modules.security import display_scan_results, scan_nodejs_deps, scan_project, scan_python_deps

    console.print("[cyan]🔍 正在扫描依赖...[/]")

    if language == "python":
        issues = scan_python_deps(dir)
    elif language == "nodejs":
        issues = scan_nodejs_deps(dir)
    else:
        issues = scan_project(dir)

    display_scan_results(issues)

    if issues:
        sys.exit(1)  # CI 场景：有漏洞时返回非零退出码


# ===================== Mock 生成 (P0-3) =====================


@main.command(name="mock")
@click.argument("spec", required=True)
@click.option("--output", "-o", default="./mock-server", help="输出目录")
@click.option("--framework", type=click.Choice(["flask", "fastapi"]), default="flask")
def mock(spec, output, framework):
    """根据 API spec 生成 Mock Server"""
    from rigor.modules.mock import generate_mock_server

    generate_mock_server(spec, output, framework)


@main.group(name="contract")
def contract():
    """API 契约检查：OpenAPI、后端路由、前端调用、运行时 smoke"""
    pass


@contract.command(name="check")
@click.option("--spec", "-s", required=True, help="OpenAPI JSON/YAML spec 路径")
@click.option("--frontend", "-f", default=None, help="前端源码目录，用于扫描 fetch/axios/client 调用")
@click.option("--backend", "-b", default=None, help="后端源码目录，用于扫描 FastAPI/Flask/Express 路由")
@click.option("--base-url", default=None, help="运行中的后端地址，用于 HTTP smoke，例如 http://localhost:8000")
@click.option("--include-unsafe", is_flag=True, help="smoke 时也请求 POST/PUT/PATCH/DELETE（默认只测 GET）")
@click.option("--forbid-manual-api", is_flag=True, help="禁止前端手写 fetch/axios API path，要求使用生成客户端")
@click.option("--fail-on-extra-backend-routes", is_flag=True, help="后端存在未写入 OpenAPI 的路由时按 high 失败处理")
@click.option("--timeout", default=5.0, type=float, help="HTTP smoke 超时时间（秒）")
@click.option("--report", "-o", default=None, help="将 Markdown 报告写入指定路径")
def contract_check(
    spec,
    frontend,
    backend,
    base_url,
    include_unsafe,
    forbid_manual_api,
    fail_on_extra_backend_routes,
    timeout,
    report,
):
    """验证开发出的应用是否满足前后端 API 契约。"""
    from rigor.modules.contract import check_contract, format_contract_report

    contract_report = check_contract(
        spec_path=spec,
        frontend_dir=frontend,
        backend_dir=backend,
        base_url=base_url,
        include_unsafe=include_unsafe,
        forbid_manual_api=forbid_manual_api,
        fail_on_extra_backend_routes=fail_on_extra_backend_routes,
        timeout=timeout,
    )
    rendered = format_contract_report(contract_report)
    console.print(Markdown(rendered))
    if report:
        Path(report).parent.mkdir(parents=True, exist_ok=True)
        Path(report).write_text(rendered, encoding="utf-8")
        console.print(f"[green]💾 契约报告已保存: {report}[/]")
    if contract_report.failed:
        raise click.ClickException("Contract check failed. Fix high/critical findings before continuing.")


@main.command(name="code-map")
@click.option("--dir", "-d", default=".", help="项目目录")
@click.option("--max-files", default=200, type=int, help="最多扫描 Python 文件数")
def code_map(dir, max_files):
    """生成轻量代码结构地图"""
    from rigor.modules.code_map import build_code_map, format_code_map

    console.print(Markdown(format_code_map(build_code_map(dir, max_files=max_files))))


@main.command(name="frame")
@click.argument("request", nargs=-1)
@click.option("--context", "-c", default=None, help="Additional context that should influence framing")
@click.option("--dir", "-d", "workspace", default=".", help="Project workspace")
@click.option(
    "--output-dir", "-o", default=None, help="Artifact output directory; defaults to <workspace>/artifacts/orchestrator"
)
@click.option("--no-save", is_flag=True, help="Print only; do not write problem-frame artifacts")
@click.option("--json", "json_output", is_flag=True, help="Print JSON instead of Markdown")
@click.option("--fail-on-clarify", is_flag=True, help="Exit non-zero when the request needs clarification")
@click.option(
    "--confirm",
    "--interactive",
    "confirm",
    is_flag=True,
    help="Ask the user to confirm the Problem Frame before it is considered approved",
)
@click.option("--clarify-missing", is_flag=True, help="Ask for missing framing fields before confirmation")
def frame(request, context, workspace, output_dir, no_save, json_output, fail_on_clarify, confirm, clarify_missing):
    """执行 Problem Framing：先定义问题，再进入 PRD/开发。"""
    from rigor.modules.framing import (
        LABEL_TO_KEY,
        format_problem_frame,
        frame_problem,
        refine_problem_frame,
        save_problem_frame,
        set_problem_frame_confirmation,
    )

    prompt = " ".join(request).strip()
    if not prompt:
        raise click.ClickException("Please provide a request to frame.")

    problem_frame = frame_problem(prompt, context=context)
    if clarify_missing and problem_frame.unknowns:
        console.print("[cyan]需要补齐几个关键问题，留空则继续按当前假设推进。[/]")
        answers = {}
        for label in problem_frame.unknowns:
            key = LABEL_TO_KEY.get(label)
            if not key:
                continue
            answer = click.prompt(f"{label}", default="", show_default=False)
            if answer.strip():
                answers[key] = answer
        if "scope" in answers and "Non-Goals" not in problem_frame.unknowns:
            non_goals = click.prompt("Non-Goals / 明确不做什么", default="", show_default=False)
            if non_goals.strip():
                answers["non_goals"] = non_goals
        if "criteria" in answers and not problem_frame.constraints:
            constraints = click.prompt("Constraints / 限制条件，可留空", default="", show_default=False)
            if constraints.strip():
                answers["constraints"] = constraints
        problem_frame = refine_problem_frame(problem_frame, answers)

    rendered_before_confirmation = False
    if confirm:
        console.print(Markdown(format_problem_frame(problem_frame)))
        rendered_before_confirmation = True
        approved = click.confirm("确认此 Problem Frame，并允许进入 PRD / DAG / 开发流程？", default=False)
        if approved:
            problem_frame = set_problem_frame_confirmation(problem_frame, confirmed=True)
            console.print("[green]✅ Problem Frame 已确认。[/]")
        else:
            note = click.prompt("需要修改或补充什么？", default="", show_default=False)
            problem_frame = set_problem_frame_confirmation(problem_frame, confirmed=False, note=note)
            console.print("[yellow]⏸️  Problem Frame 未确认，流程应暂停。[/]")

    if json_output:
        console.print(json.dumps(problem_frame.to_dict(), ensure_ascii=False, indent=2))
    elif not rendered_before_confirmation or problem_frame.confirmation_status != "pending":
        console.print(Markdown(format_problem_frame(problem_frame)))

    if not no_save:
        target_dir = (
            Path(output_dir).expanduser() if output_dir else Path(workspace).expanduser() / "artifacts" / "orchestrator"
        )
        md_path, json_path = save_problem_frame(problem_frame, target_dir)
        console.print(f"[green]💾 Problem frame saved: {md_path}[/]")
        console.print(f"[green]💾 Problem frame JSON saved: {json_path}[/]")

    if fail_on_clarify and problem_frame.should_block_execution:
        raise click.ClickException("Problem framing requires clarification before execution.")
    if confirm and not problem_frame.confirmed_by_user:
        raise click.ClickException("Problem framing was not confirmed by the user.")


# ===================== 报告生成 (P0-4) =====================


@main.group()
def report():
    """日报/周报生成"""
    pass


@report.command("daily")
@click.option("--dir", "-d", default=".", help="项目目录")
@click.option("--author", "-a", default=None, help="作者过滤")
@click.option("--save/--no-save", default=True, help="保存到文件")
def report_daily(dir, author, save):
    """生成日报"""
    from rigor.modules.reports import generate_daily_report, save_report

    report = generate_daily_report(dir, author)
    console.print(Markdown(report))

    if save:
        path = save_report(report, project_dir=dir)
        console.print(f"\n[green]💾 已保存: {path}[/]")


@report.command("weekly")
@click.option("--dir", "-d", default=".", help="项目目录")
@click.option("--author", "-a", default=None, help="作者过滤")
@click.option("--save/--no-save", default=True, help="保存到文件")
def report_weekly(dir, author, save):
    """生成周报"""
    from rigor.modules.reports import generate_weekly_report, save_report

    report = generate_weekly_report(dir, author)
    console.print(Markdown(report))

    if save:
        path = save_report(report, project_dir=dir)
        console.print(f"\n[green]💾 已保存: {path}[/]")


# ===================== 项目脚手架 =====================


def build_init_project_command(
    project_name: str,
    *,
    target_dir: str | None = None,
    projects_dir: str | None = None,
) -> list[str]:
    """Build the project scaffold command without invoking a shell."""
    script = PROJECT_ROOT / "scripts" / "init-project.sh"
    argv = ["bash", str(script), project_name]
    if target_dir:
        argv.extend(["--dir", target_dir])
    elif projects_dir:
        argv.extend(["--base-dir", projects_dir])
    return argv


@main.command(name="init")
@click.argument("project_name")
@click.option(
    "--dir",
    "target_dir",
    default=None,
    help="Exact target directory. Defaults to ~/projects/<project-name>.",
)
@click.option(
    "--projects-dir",
    default=None,
    envvar="RIGOR_PROJECTS_DIR",
    help="Base directory for generated projects. Defaults to ~/projects.",
)
def init_project(project_name, target_dir, projects_dir):
    """创建新项目脚手架，默认输出到 ~/projects/<项目名>"""
    script = PROJECT_ROOT / "scripts" / "init-project.sh"
    if script.exists():
        os.execv("bash", build_init_project_command(project_name, target_dir=target_dir, projects_dir=projects_dir))
    else:
        console.print("[red]❌ 找不到脚手架脚本[/]")


@main.command(context_settings=CHAT_CONTEXT_SETTINGS)
@click.argument("prompt", nargs=-1)
@click.option(
    "--profile",
    "-p",
    default="orchestrator",
    show_default=True,
    help="Hermes profile to use; Rigor syncs current Hermes login/provider into it before launch",
)
@click.option(
    "--no-sync-profile", is_flag=True, help="Do not sync current Hermes config/auth into the selected profile"
)
@click.option("--query", "-q", default=None, help="Run one prompt and exit")
@click.option("--resume", "-r", default=None, help="Resume a previous Hermes session")
@click.option("--continue", "continue_last", "-c", is_flag=True, help="Continue the latest Hermes session")
@click.option("--model", "-m", default=None, help="Override model for this chat")
@click.option("--provider", default=None, help="Override provider for this chat")
@click.option("--toolsets", "-t", default=None, help="Comma-separated Hermes toolsets")
@click.option("--max-turns", type=int, default=None, help="Maximum tool-calling turns")
@click.option("--hermes-tui", is_flag=True, help="Use Hermes' own TUI instead of the classic chat CLI")
@click.option("--accept-hooks", is_flag=True, help="Auto-approve configured Hermes shell hooks")
@click.pass_context
def chat(
    ctx,
    prompt,
    profile,
    no_sync_profile,
    query,
    resume,
    continue_last,
    model,
    provider,
    toolsets,
    max_turns,
    hermes_tui,
    accept_hooks,
):
    """Open Rigor orchestrator chat with current Hermes credentials."""
    if profile and not no_sync_profile:
        sync_hermes_profile_runtime(profile)
    prompt_text = query or " ".join(prompt).strip() or None
    argv = build_hermes_chat_command(
        profile=profile,
        query=prompt_text,
        resume=resume,
        continue_last=continue_last,
        model=model,
        provider=provider,
        toolsets=toolsets,
        max_turns=max_turns,
        hermes_tui=hermes_tui,
        accept_hooks=accept_hooks,
        extra_args=list(ctx.args),
    )
    _exec_hermes_chat(argv)


@main.command(context_settings=CHAT_CONTEXT_SETTINGS)
@click.pass_context
def tui(ctx):
    """Deprecated alias for `rigor chat`."""
    console.print("[yellow]Rigor custom TUI is deprecated. Launching Hermes orchestrator chat instead.[/]")
    sync_hermes_profile_runtime("orchestrator")
    _exec_hermes_chat(build_hermes_chat_command(extra_args=list(ctx.args)))


# ===================== CI/CD Webhook =====================


@main.command(name="setup")
@click.option("--dir", "-d", default=".", help="Project directory")
def setup(dir):
    """Run the 5-layer autonomous environment setup (Deps, System, Env, DB, Service)"""
    from rigor.modules.terminal import AgentTerminal

    console.print("[bold cyan]🤖 Starting Rigor Autonomous Environment Setup...[/]")

    term = AgentTerminal(workdir=dir)
    results = term.setup_environment()

    for r in results:
        layer_name = r["layer"]
        res = r["result"]
        if res.get("success"):
            console.print(f"[green]✅ [{layer_name}][/green] {res.get('message', 'OK')}")
        else:
            console.print(f"[red]❌ [{layer_name}][/red] {res.get('error', 'Failed')}")
            if res.get("suggestion"):
                console.print(f"[yellow]   💡 Suggestion: {res['suggestion']}[/yellow]")


@main.command(name="knowledge")
@click.option("--vault", "-v", default=None, help="Obsidian Vault 路径")
@click.argument("query", required=False)
def knowledge(query, vault):
    """管理知识库 (索引 / 全文搜索)"""
    from rigor.modules.knowledge import KnowledgeEngine

    engine = KnowledgeEngine(vault_path=vault)

    if query:
        # Search mode
        console.print(f"[cyan]🔍 正在搜索: '{query}'[/]")
        results = engine.search(query)
        if not results:
            console.print("[yellow]未找到相关知识。[/]")
        else:
            console.print(f"[green]✅ 找到 {len(results)} 条结果:[/]")
            for i, r in enumerate(results):
                console.print(f"\n[bold]{i + 1}. {r['title']}[/] ({r['category']})")
                console.print(f"   路径: {r['path']}")
                console.print(f"   预览: {r['content_preview']}")
    else:
        # Index & Stats mode
        console.print("[cyan]📚 正在索引知识库...[/]")
        stats = engine.get_stats()
        if stats.get("total_documents", 0) == 0:
            engine.index_vault()
            stats = engine.get_stats()
        console.print("[green]✅ 知识库状态:[/]")
        console.print(f"   总文档: {stats.get('total_documents', 0)}")
        console.print(f"   索引路径: {stats.get('db_path', 'N/A')}")

    engine.close()


@main.command(name="watch-fix")
@click.option("--db", default="~/.hermes/kanban.db", help="Kanban DB 路径")
@click.option("--workspace", "-w", default=".", help="项目工作目录")
@click.option("--interval", "-i", default=15, type=int, help="轮询间隔 (秒)")
@click.option("--max-retries", "-r", default=3, type=int, help="最大重试次数")
@click.option("--dry-run", is_flag=True, help="仅模拟，不写数据库")
def watch_fix(db, workspace, interval, max_retries, dry_run):
    """启动 Auto-Fix 后台守护进程 (自修复循环)"""
    from rigor.autofix import watch_fix as _watch_fix

    _watch_fix(db_path=db, workspace=workspace, interval=interval, max_retries=max_retries, dry_run=dry_run)


@main.command(name="webhook")
@click.option("--port", "-p", default=9999, help="Webhook 监听端口 (默认: 9999)")
@click.option("--ci-platform", type=click.Choice(["github", "gitlab", "auto"]), default="auto", help="CI 平台")
@click.option("--secret", default=None, help="Webhook 签名密钥（也可用 RIGOR_WEBHOOK_SECRET）")
def webhook(port, ci_platform, secret):
    """启动 CI/CD Webhook 监听服务"""
    from rigor.modules.webhook import CIWebhookManager, parse_github_payload, parse_gitlab_payload

    def handle_ci_event(platform: str, payload: dict[str, Any]):
        """处理 CI 事件回调"""
        if ci_platform != "auto":
            platform = ci_platform

        if platform == "github":
            event = parse_github_payload(payload)
        else:
            event = parse_gitlab_payload(payload)

        status_icon = "✅" if event.get("status") in ("success", "passed") else "❌"
        console.print(
            f"[bold]{status_icon} CI 结果: "
            f"[cyan]{event['repo']}[/] | "
            f"{event['name']} | "
            f"[{'green' if event['status'] in ('success', 'passed') else 'red'}]{event['status']}[/] | "
            f"分支: {event['ref']}"
        )
        console.print(f"  URL: {event.get('url', 'N/A')}")

        # Auto-Fix: 当 CI 失败时自动创建修复任务
        if event.get("status") not in ("success", "passed"):
            from rigor.autofix import create_fix_task_from_ci

            error_detail = event.get("name", "Unknown CI error")
            result = create_fix_task_from_ci(
                repo=event["repo"],
                pr_number=event.get("pr_number", 0),
                pr_url=event.get("url", ""),
                ci_error=error_detail,
                ci_platform=platform,
            )
            if result.get("success"):
                console.print(f"[green]✅ 自动修复任务已创建: #{result.get('task_id')}[/]")
            else:
                console.print(f"[yellow]⚠️  自动修复任务创建失败: {result.get('error')}[/]")

    manager = CIWebhookManager(port=port, secret=secret)
    manager.start(handle_ci_event)

    console.print("[dim]按 Ctrl+C 停止服务[/]")
    try:
        import time

        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        manager.stop()


if __name__ == "__main__":
    main()
