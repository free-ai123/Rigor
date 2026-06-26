"""多 Git 平台抽象层 — 统一 GitHub / GitLab / Gitea 接口"""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any


class GitPlatform(ABC):
    """所有 Git 平台必须实现的接口"""

    @abstractmethod
    def get_token(self) -> str:
        pass

    @abstractmethod
    def create_pr(
        self,
        repo: str,
        title: str,
        body: str,
        source_branch: str,
        target_branch: str = "main",
    ) -> Dict[str, Any]:
        """创建 Pull/Merge Request"""
        pass

    @abstractmethod
    def get_pr(self, repo: str, pr_number: int) -> Dict[str, Any]:
        pass

    @abstractmethod
    def list_prs(self, repo: str, state: str = "open") -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def add_pr_review(
        self, repo: str, pr_number: int, body: str, event: str = "COMMENT"
    ) -> Dict[str, Any]:
        """添加 Review 评论 (APPROVE / REQUEST_CHANGES / COMMENT)"""
        pass

    @abstractmethod
    def get_repo(self, repo: str) -> Dict[str, Any]:
        pass

    @abstractmethod
    def get_files_in_pr(self, repo: str, pr_number: int) -> List[Dict[str, Any]]:
        """获取 PR 中变更的文件列表"""
        pass

    @abstractmethod
    def create_issue(
        self, repo: str, title: str, body: str, labels: List[str] = None
    ) -> Dict[str, Any]:
        pass


def detect_platform(repo_url: str = None) -> str:
    """自动检测 Git 平台类型"""
    if not repo_url:
        import subprocess
        try:
            result = subprocess.run(
                ["git", "remote", "get-url", "origin"],
                capture_output=True, text=True, timeout=5
            )
            repo_url = result.stdout.strip()
        except Exception:
            return "unknown"

    if "gitlab" in repo_url.lower():
        return "gitlab"
    elif "gitea" in repo_url.lower() or "gitee" in repo_url.lower():
        return "gitea"
    elif "github" in repo_url.lower():
        return "github"
    return "unknown"
