"""GitHub 平台实现 — 使用 REST API（无需额外依赖）"""

import os
from typing import Any, Optional

import requests

from .platform import GitPlatform


class GitHub(GitPlatform):
    """GitHub API 实现，支持 Token 认证"""

    API_BASE = "https://api.github.com"

    def __init__(self, token: str = None):
        self._token = token or os.getenv("GITHUB_TOKEN", "")
        self._headers = {
            "Authorization": f"Bearer {self._token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    def get_token(self) -> str:
        return self._token

    def create_pr(
        self,
        repo: str,
        title: str,
        body: str,
        source_branch: str,
        target_branch: str = "main",
    ) -> dict[str, Any]:
        url = f"{self.API_BASE}/repos/{repo}/pulls"
        resp = requests.post(
            url,
            headers=self._headers,
            json={
                "title": title,
                "body": body,
                "head": source_branch,
                "base": target_branch,
            },
        )
        resp.raise_for_status()
        return resp.json()

    def get_pr(self, repo: str, pr_number: int) -> dict[str, Any]:
        url = f"{self.API_BASE}/repos/{repo}/pulls/{pr_number}"
        resp = requests.get(url, headers=self._headers)
        resp.raise_for_status()
        return resp.json()

    def list_prs(self, repo: str, state: str = "open") -> list[dict[str, Any]]:
        url = f"{self.API_BASE}/repos/{repo}/pulls"
        resp = requests.get(url, headers=self._headers, params={"state": state})
        resp.raise_for_status()
        return resp.json()

    def add_pr_review(self, repo: str, pr_number: int, body: str, event: str = "COMMENT") -> dict[str, Any]:
        url = f"{self.API_BASE}/repos/{repo}/pulls/{pr_number}/reviews"
        resp = requests.post(
            url,
            headers=self._headers,
            json={
                "body": body,
                "event": event,  # APPROVE, REQUEST_CHANGES, COMMENT
            },
        )
        resp.raise_for_status()
        return resp.json()

    def get_repo(self, repo: str) -> dict[str, Any]:
        url = f"{self.API_BASE}/repos/{repo}"
        resp = requests.get(url, headers=self._headers)
        resp.raise_for_status()
        return resp.json()

    def get_files_in_pr(self, repo: str, pr_number: int) -> list[dict[str, Any]]:
        url = f"{self.API_BASE}/repos/{repo}/pulls/{pr_number}/files"
        resp = requests.get(url, headers=self._headers)
        resp.raise_for_status()
        return resp.json()

    def create_issue(self, repo: str, title: str, body: str, labels: Optional[list[str]] = None) -> dict[str, Any]:
        url = f"{self.API_BASE}/repos/{repo}/issues"
        data: dict[str, Any] = {"title": title, "body": body}
        if labels:
            data["labels"] = labels
        resp = requests.post(url, headers=self._headers, json=data)
        resp.raise_for_status()
        return resp.json()
