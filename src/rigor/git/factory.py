"""多平台 PR 工厂 — 根据仓库 URL 自动选择平台"""

from typing import Dict, Any, Optional, List
from .platform import GitPlatform, detect_platform
from .github import GitHub
from .gitlab import GitLab


def create_platform(repo_url: str = None, token: str = None, platform_type: str = None) -> GitPlatform:
    """工厂方法：自动检测并创建对应的平台客户端"""
    
    if platform_type:
        ptype = platform_type.lower()
    else:
        ptype = detect_platform(repo_url)
    
    if ptype == "github":
        return GitHub(token=token)
    elif ptype == "gitlab":
        return GitLab(token=token)
    else:
        raise ValueError(f"不支持的平台: {ptype}。支持的: github, gitlab")


def get_repo_name_from_url(repo_url: str) -> str:
    """从 git URL 提取 owner/repo 格式"""
    import re
    # SSH: git@github.com:owner/repo.git
    m = re.search(r'[:/](\w+/\w+?)(?:\.git)?$', repo_url)
    if m:
        return m.group(1)
    # HTTPS: https://github.com/owner/repo.git
    m = re.search(r'github\.com[:/](\w+/\w+?)(?:\.git)?$', repo_url)
    if m:
        return m.group(1)
    raise ValueError(f"无法从 URL 提取仓库名: {repo_url}")
