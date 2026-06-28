"""Tests for webhook platform detection and signature verification."""

import hashlib
import hmac
import json

from rigor.modules.webhook import WebhookHandler


def _handler(headers: dict[str, str], secret: str | None = None) -> WebhookHandler:
    handler = object.__new__(WebhookHandler)
    handler.headers = headers
    handler.secret = secret
    return handler


def test_webhook_rejects_invalid_github_signature():
    body = json.dumps({"repository": {"full_name": "owner/repo"}}).encode("utf-8")
    handler = _handler(
        {
            "X-GitHub-Event": "check_run",
            "X-Hub-Signature-256": "sha256=bad",
        },
        secret="top-secret",
    )

    assert handler._detect_platform() == "github"
    assert handler._verify_signature("github", body) is False


def test_webhook_accepts_valid_github_signature():
    secret = "top-secret"
    body = json.dumps({"repository": {"full_name": "owner/repo"}}).encode("utf-8")
    signature = "sha256=" + hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
    handler = _handler(
        {
            "X-GitHub-Event": "check_run",
            "X-Hub-Signature-256": signature,
        },
        secret=secret,
    )

    assert handler._detect_platform() == "github"
    assert handler._verify_signature("github", body) is True


def test_webhook_accepts_valid_gitlab_token():
    body = json.dumps({"project": {"path_with_namespace": "group/repo"}}).encode("utf-8")
    handler = _handler(
        {
            "X-Gitlab-Event": "Pipeline Hook",
            "X-Gitlab-Token": "gitlab-secret",
        },
        secret="gitlab-secret",
    )

    assert handler._detect_platform() == "gitlab"
    assert handler._verify_signature("gitlab", body) is True
