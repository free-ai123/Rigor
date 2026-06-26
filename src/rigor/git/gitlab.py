"""GitLab 平台实现 — 使用 GitLab REST API v4"""

import os
from typing import Any, Optional

import requests

from .platform import GitPlatform


class GitLab(GitPlatform):
    """GitLab API v4 实现"""

    def __init__(self, token: str = None, base_url: str = None):
        self._token = token or os.getenv("GITLAB_TOKEN", "")
        self._base_url = (base_url or os.getenv("GITLAB_URL", "https://gitlab.com")).rstrip("/")
        self._api_url = f"{self._base_url}/api/v4"
        self._headers = {"PRIVATE-TOKEN": self._token}

    def get_token(self) -> str:
        return self._token

    def _project_id(self, repo: str) -> str:
        """GitLab 使用 URL-encoded path 或 numeric ID"""
        return requests.utils.quote(repo, safe="")

    def create_pr(
        self,
        repo: str,
        title: str,
        body: str,
        source_branch: str,
        target_branch: str = "main",
    ) -> dict[str, Any]:
        """GitLab 叫 Merge Request"""
        pid = self._project_id(repo)
        url = f"{self._api_url}/projects/{pid}/merge_requests"
        resp = requests.post(
            url,
            headers=self._headers,
            json={
                "title": title,
                "description": body,
                "source_branch": source_branch,
                "target_branch": target_branch,
            },
        )
        resp.raise_for_status()
        return resp.json()

    def get_pr(self, repo: str, pr_number: int) -> dict[str, Any]:
        pid = self._project_id(repo)
        url = f"{self._api_url}/projects/{pid}/merge_requests/{pr_number}"
        resp = requests.get(url, headers=self._headers)
        resp.raise_for_status()
        return resp.json()

    def list_prs(self, repo: str, state: str = "opened") -> list[dict[str, Any]]:
        pid = self._project_id(repo)
        # GitLab uses different state names
        state_map = {"open": "opened", "closed": "closed", "all": "all"}
        url = f"{self._api_url}/projects/{pid}/merge_requests"
        resp = requests.get(url, headers=self._headers, params={"state": state_map.get(state, state)})
        resp.raise_for_status()
        return resp.json()

    def add_pr_review(self, repo: str, pr_number: int, body: str, event: str = "COMMENT") -> dict[str, Any]:
        """GitLab 使用 MR notes/discussion"""
        pid = self._project_id(repo)
        url = f"{self._api_url}/projects/{pid}/merge_requests/{pr_number}/notes"
        resp = requests.post(url, headers=self._headers, json={"body": body})
        resp.raise_for_status()
        return resp.json()

    def get_repo(self, repo: str) -> dict[str, Any]:
        pid = self._project_id(repo)
        url = f"{self._api_url}/projects/{pid}"
        resp = requests.get(url, headers=self._headers)
        resp.raise_for_status()
        return resp.json()

    def get_files_in_pr(self, repo: str, pr_number: int) -> list[dict[str, Any]]:
        pid = self._project_id(repo)
        url = f"{self._api_url}/projects/{pid}/merge_requests/{pr_number}/changes"
        resp = requests.get(url, headers=self._headers)
        resp.raise_for_status()
        data = resp.json()
        return data.get("changes", [])

    def create_issue(self, repo: str, title: str, body: str, labels: Optional[list[str]] = None) -> dict[str, Any]:
        pid = self._project_id(repo)
        url = f"{self._api_url}/projects/{pid}/issues"
        data: dict[str, Any] = {"title": title, "description": body}
        if labels:
            data["labels"] = ",".join(labels)
        resp = requests.post(url, headers=self._headers, json=data)
        resp.raise_for_status()
        return resp.json()
