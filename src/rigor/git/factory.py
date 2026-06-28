"""多平台 PR 工厂 — 根据仓库 URL 自动选择平台"""

from .github import GitHub
from .gitlab import GitLab
from .platform import GitPlatform, detect_platform


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
    from urllib.parse import urlparse

    if not repo_url:
        raise ValueError("仓库 URL 为空")

    repo_url = repo_url.strip()

    # SSH/SCP: git@github.com:owner/repo.git or git@gitlab.com:group/sub/repo.git
    m = re.match(r"[^@]+@[^:]+:(?P<path>.+?)(?:\.git)?$", repo_url)
    if m:
        return m.group("path").rstrip("/")

    # HTTPS: https://github.com/owner/repo.git
    parsed = urlparse(repo_url)
    if parsed.scheme and parsed.path:
        path = parsed.path.strip("/")
        if path.endswith(".git"):
            path = path[:-4]
        if "/" in path:
            return path

    # Already owner/repo or group/subgroup/repo.
    if "/" in repo_url and not re.search(r"\s", repo_url):
        return repo_url.removesuffix(".git").strip("/")

    raise ValueError(f"无法从 URL 提取仓库名: {repo_url}")
