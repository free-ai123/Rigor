"""Tests for Git platform helpers."""

from rigor.git.factory import get_repo_name_from_url


def test_get_repo_name_from_hyphenated_github_url():
    assert get_repo_name_from_url("https://github.com/free-ai123/Rigor.git") == "free-ai123/Rigor"


def test_get_repo_name_from_gitlab_subgroup_ssh_url():
    assert get_repo_name_from_url("git@gitlab.com:group/sub-group/my-repo.git") == "group/sub-group/my-repo"
