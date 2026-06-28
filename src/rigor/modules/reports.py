"""日报/周报自动生成 — 基于 Git 提交和任务状态"""

import os
import subprocess
from datetime import datetime, timedelta
from typing import Any

from rich.console import Console

console = Console()


def get_commits_since(days: int = 1, project_dir: str = ".") -> list[dict[str, str]]:
    """获取最近 N 天的 Git 提交"""
    since = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    result = subprocess.run(
        ["git", "log", f"--since={since}", "--pretty=format:%H|%s|%an|%ad", "--date=short"],
        capture_output=True,
        text=True,
        timeout=10,
        cwd=project_dir,
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


def get_diff_stats(days: int = 1, project_dir: str = ".") -> dict[str, Any]:
    """获取最近 N 天的代码变更统计"""
    since = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    result = subprocess.run(
        ["git", "log", f"--since={since}", "--numstat", "--pretty=format:"],
        capture_output=True,
        text=True,
        timeout=10,
        cwd=project_dir,
    )

    stats = {"files": 0, "insertions": 0, "deletions": 0}
    changed_files: set[str] = set()
    for line in result.stdout.splitlines():
        parts = line.split("\t")
        if len(parts) != 3:
            continue
        added, deleted, filename = parts
        changed_files.add(filename)
        if added.isdigit():
            stats["insertions"] += int(added)
        if deleted.isdigit():
            stats["deletions"] += int(deleted)
    stats["files"] = len(changed_files)
    return stats


def generate_daily_report(project_dir: str = ".", author: str = None) -> str:
    """生成日报"""
    commits = get_commits_since(1, project_dir)
    stats = get_diff_stats(1, project_dir)
    today = datetime.now().strftime("%Y-%m-%d")

    report = []
    report.append(f"# 📋 日报 — {today}\n")

    if author:
        commits = [c for c in commits if c["author"] == author]
        report.append(f"**作者**: {author}\n")

    # 今日提交
    report.append("## ✅ 今日完成\n")
    if commits:
        for c in commits:
            report.append(f"- `{c['hash']}` {c['message']}")
    else:
        report.append("- 无提交记录\n")

    # 代码变更
    report.append("\n## 📊 代码变更\n")
    report.append(f"- 变更文件: {stats['files']} 个")
    report.append(f"- 新增行数: +{stats['insertions']}")
    report.append(f"- 删除行数: -{stats['deletions']}")

    # 明日计划（占位）
    report.append("\n## 📅 明日计划\n")
    report.append("- [ ] 待定\n")

    # 风险/阻塞
    report.append("\n## ⚠️ 风险与阻塞\n")
    report.append("- 无\n")

    return "\n".join(report)


def generate_weekly_report(project_dir: str = ".", author: str = None) -> str:
    """生成周报"""
    commits = get_commits_since(7, project_dir)
    stats = get_diff_stats(7, project_dir)
    week_start = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    week_end = datetime.now().strftime("%Y-%m-%d")

    report = []
    report.append(f"# 📊 周报 ({week_start} ~ {week_end})\n")

    if author:
        commits = [c for c in commits if c["author"] == author]
        report.append(f"**作者**: {author}\n")

    # 本周工作总结
    report.append("## ✅ 本周完成\n")
    if commits:
        for c in commits:
            report.append(f"- `{c['hash']}` {c['message']} ({c['author']}, {c['date']})")
    else:
        report.append("- 无提交记录\n")

    # 代码统计
    report.append("\n## 📈 代码统计\n")
    report.append(f"- 变更文件: {stats['files']} 个")
    report.append(f"- 新增行数: +{stats['insertions']}")
    report.append(f"- 删除行数: -{stats['deletions']}")

    # 按作者统计
    if not author:
        report.append("\n## 👥 贡献者统计\n")
        author_counts: dict[str, int] = {}
        for c in commits:
            author_counts[c["author"]] = author_counts.get(c["author"], 0) + 1
        for name, count in sorted(author_counts.items(), key=lambda x: -x[1]):
            report.append(f"- {name}: {count} 次提交")

    # 下周计划
    report.append("\n## 📅 下周计划\n")
    report.append("- [ ] 待定\n")

    # 风险与问题
    report.append("\n## ⚠️ 风险与问题\n")
    report.append("- 无\n")

    return "\n".join(report)


def save_report(report: str, filename: str = None, project_dir: str = ".") -> str:
    """保存报告到文件"""
    if not filename:
        today = datetime.now().strftime("%Y-%m-%d")
        filename = f"report-{today}.md"

    output_path = os.path.join(project_dir, filename)
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

    with open(output_path, "w") as f:
        f.write(report)

    return output_path
