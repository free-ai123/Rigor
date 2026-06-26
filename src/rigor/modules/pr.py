"""PR 自动生成 + Review — 支持 GitHub/GitLab 多平台"""

import os
import subprocess
from typing import Any

from rich.console import Console

from rigor.git.factory import create_platform, get_repo_name_from_url

console = Console()


def get_current_branch() -> str:
    """获取当前 Git 分支名"""
    result = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"], capture_output=True, text=True, timeout=10)
    return result.stdout.strip()


def get_commit_range(branch: str, base: str = "main") -> list[dict[str, str]]:
    """获取两个分支之间的提交记录"""
    result = subprocess.run(
        ["git", "log", f"{base}..{branch}", "--pretty=format:%H|%s|%an|%ad", "--date=short"],
        capture_output=True,
        text=True,
        timeout=10,
    )
    commits = []
    for line in result.stdout.strip().split("\n"):
        if not line:
            continue
        parts = line.split("|", 3)
        if len(parts) == 4:
            commits.append(
                {
                    "hash": parts[0][:8],
                    "message": parts[1],
                    "author": parts[2],
                    "date": parts[3],
                }
            )
    return commits


def get_diff_summary(branch: str, base: str = "main") -> dict[str, Any]:
    """获取代码变更摘要"""
    # 统计文件变更
    result = subprocess.run(["git", "diff", "--stat", f"{base}..{branch}"], capture_output=True, text=True, timeout=10)
    # 统计行数
    result_add = subprocess.run(
        ["git", "diff", "--shortstat", f"{base}..{branch}"], capture_output=True, text=True, timeout=10
    )

    # 按文件类型分类
    result_files = subprocess.run(
        ["git", "diff", "--name-only", f"{base}..{branch}"], capture_output=True, text=True, timeout=10
    )

    files_by_ext: dict[str, list[str]] = {}
    for f in result_files.stdout.strip().split("\n"):
        if not f:
            continue
        ext = os.path.splitext(f)[1] or "no-ext"
        files_by_ext.setdefault(ext, []).append(f)

    return {
        "stats": result_add.stdout.strip(),
        "stat_detail": result.stdout.strip(),
        "files": result_files.stdout.strip().split("\n"),
        "files_by_ext": files_by_ext,
        "total_files": len([f for f in result_files.stdout.strip().split("\n") if f]),
    }


def generate_pr_body(branch: str, base: str = "main", title: str = None) -> str:
    """自动生成 PR 描述"""
    commits = get_commit_range(branch, base)
    diff = get_diff_summary(branch, base)

    if not title:
        # 用第一个提交消息作为标题
        title = commits[0]["message"] if commits else f"Update from {branch}"

    body_parts = []

    # Header
    body_parts.append("## 📝 变更摘要\n")
    body_parts.append(f"**分支**: `{base}` → `{branch}`\n")
    body_parts.append(f"**变更文件**: {diff['total_files']} 个\n")
    body_parts.append(f"**提交数量**: {len(commits)} 个\n")

    # Commits
    if commits:
        body_parts.append("## 📋 提交记录\n")
        for c in commits:
            body_parts.append(f"- `{c['hash']}` {c['message']} ({c['author']}, {c['date']})")
        body_parts.append("")

    # File changes by type
    if diff["files_by_ext"]:
        body_parts.append("## 📁 文件变更\n")
        for ext, files in sorted(diff["files_by_ext"].items()):
            body_parts.append(f"**{ext}** ({len(files)} files)")
            for f in files[:5]:
                body_parts.append(f"  - `{f}`")
            if len(files) > 5:
                body_parts.append(f"  - ... 及其他 {len(files) - 5} 个文件")
            body_parts.append("")

    # Auto checklist
    body_parts.append("## ✅ 检查清单\n")
    body_parts.append("- [ ] 代码已通过本地测试")
    body_parts.append("- [ ] 没有遗留的 TODO/FIXME")
    body_parts.append("- [ ] 依赖更新已记录")
    body_parts.append("- [ ] 文档已更新（如需要）")

    return title, "\n".join(body_parts)


def create_pr(
    repo_url: str = None,
    branch: str = None,
    base: str = "main",
    token: str = None,
    platform_type: str = None,
    auto_review: bool = True,
) -> dict[str, Any]:
    """创建 PR 并自动添加 AI Review"""

    if not branch:
        branch = get_current_branch()
    if branch == base:
        console.print(f"[yellow]当前分支与目标分支相同 ({base})，跳过 PR 创建[/]")
        return {"status": "skipped", "reason": "same_branch"}

    # 自动生成标题和描述
    title, body = generate_pr_body(branch, base)

    # 确定仓库名
    if not repo_url:
        result = subprocess.run(["git", "remote", "get-url", "origin"], capture_output=True, text=True, timeout=5)
        repo_url = result.stdout.strip()

    repo = get_repo_name_from_url(repo_url)

    # 创建平台客户端
    platform = create_platform(repo_url, token, platform_type)

    console.print("\n[bold cyan]📤 正在创建 PR...[/]")
    console.print(f"  仓库: {repo}")
    console.print(f"  分支: {base} ← {branch}")
    console.print(f"  标题: {title}")

    try:
        pr_data = platform.create_pr(repo, title, body, branch, base)
        pr_number = pr_data.get("number") or pr_data.get("iid")
        pr_url = pr_data.get("html_url") or pr_data.get("web_url", "")

        console.print(f"[green]✅ PR 创建成功! #{pr_number}[/]")
        console.print(f"  URL: {pr_url}")

        # 自动 Review
        if auto_review:
            console.print("\n[bold cyan]🔍 正在执行自动 Review...[/]")
            review_body = _generate_review(platform, repo, pr_number, branch, base)
            platform.add_pr_review(repo, pr_number, review_body, "COMMENT")
            console.print("[green]✅ Review 评论已添加[/]")

        return {
            "status": "created",
            "pr_number": pr_number,
            "pr_url": pr_url,
            "title": title,
            "review_added": auto_review,
        }

    except Exception as e:
        console.print(f"[red]❌ PR 创建失败: {e}[/]")
        return {"status": "error", "error": str(e)}


def _generate_review(platform, repo: str, pr_number: int, branch: str, base: str) -> str:
    """生成 AI Review 评论"""
    diff = get_diff_summary(branch, base)

    review_parts = [
        "## 🤖 Rigor 自动 Review\n",
        f"**变更文件**: {diff['total_files']} 个\n",
    ]

    # 安全检查
    security_issues = _check_security(diff)
    if security_issues:
        review_parts.append("### 🔒 安全问题\n")
        for issue in security_issues:
            review_parts.append(f"- ⚠️ {issue}")
        review_parts.append("")

    # 代码质量检查
    quality_issues = _check_quality(diff)
    if quality_issues:
        review_parts.append("### 📊 代码质量\n")
        for issue in quality_issues:
            review_parts.append(f"- 💡 {issue}")
        review_parts.append("")

    # 建议
    review_parts.append("### 💡 建议\n")
    review_parts.append("- 确保所有新增函数都有文档字符串")
    review_parts.append("- 检查是否有硬编码的密钥或 Token")
    review_parts.append("- 确认异常处理覆盖边界情况")

    return "\n".join(review_parts)


def _check_security(diff: dict[str, Any]) -> list[str]:
    """基础安全检查"""
    issues = []

    for f in diff.get("files", []):
        if ".env" in f and not f.startswith(".env."):
            issues.append(f"⚠️ `{f}` 可能包含敏感信息，请确认已加入 .gitignore")
        if "password" in f.lower() or "secret" in f.lower() or "token" in f.lower():
            issues.append(f"🔑 `{f}` 包含敏感词，请确认没有硬编码密钥")

    return issues


def _check_quality(diff: dict[str, Any]) -> list[str]:
    """基础代码质量检查"""
    issues = []

    py_files = [f for f in diff.get("files", []) if f.endswith(".py")]
    if py_files:
        issues.append(f"🐍 {len(py_files)} 个 Python 文件变更，建议运行 `ruff check`")

    js_files = [f for f in diff.get("files", []) if f.endswith((".js", ".ts"))]
    if js_files:
        issues.append(f"📜 {len(js_files)} 个 JS/TS 文件变更，建议运行 `eslint`")

    return issues
