"""Rigor CLI v2.0 — 统一入口"""

import click
import sys
import os
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.markdown import Markdown

console = Console()

# 确保项目根目录在 PATH 中
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


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
    script = os.path.join(PROJECT_ROOT, "scripts", "setup-expert-team.sh")
    if not os.path.exists(script):
        console.print("[red]❌ 找不到安装脚本[/]")
        return
    console.print("[cyan]正在启动智能安装向导...[/]")
    os.execv("bash", ["bash", script])


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
            console.print(f"  🤖 自动 Review: 已添加")
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
    from rigor.git.factory import create_platform, get_repo_name_from_url
    from rigor.modules.pr import _generate_review
    
    platform_client = create_platform(platform_type=platform, token=token)
    
    # 获取 PR 信息
    pr_data = platform_client.get_pr(repo, pr)
    source = pr_data.get("head", {}).get("ref", "unknown")
    
    review = _generate_review(platform_client, repo, pr, source, "main")
    result = platform_client.add_pr_review(repo, pr, review, "COMMENT")
    
    console.print(f"[green]✅ Review 评论已添加到 #{pr}[/]")


# ===================== 安全扫描 (P0-2) =====================

@main.command(name="scan")
@click.option("--dir", "-d", default=".", help="项目目录")
@click.option("--language", type=click.Choice(["python", "nodejs", "all"]), default="all")
def scan(dir, language):
    """依赖安全扫描"""
    from rigor.modules.security import scan_project, scan_python_deps, scan_nodejs_deps, display_scan_results
    
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

@main.command(name="init")
@click.argument("project_name")
def init_project(project_name):
    """创建新项目脚手架"""
    script = os.path.join(PROJECT_ROOT, "scripts", "init-project.sh")
    if os.path.exists(script):
        os.execv("bash", ["bash", script, project_name])
    else:
        console.print("[red]❌ 找不到脚手架脚本[/]")


@main.command()
def tui():
    """启动实时 TUI 仪表盘"""
    from rigor.tui.app import RigorTUI
    app = RigorTUI()
    app.run()
