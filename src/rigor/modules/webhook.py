"""CI/CD Webhook Listener for Rigor."""

import hashlib
import hmac
import http.server
import json
import os
import socketserver
import threading
from collections.abc import Callable
from typing import Any

from rich.console import Console

console = Console()


class ReusableTCPServer(socketserver.TCPServer):
    allow_reuse_address = True


class WebhookHandler(http.server.BaseHTTPRequestHandler):
    """Handles incoming CI/CD webhooks."""

    callback: Callable[[str, dict[str, Any]], None] | None = None
    secret: str | None = None
    max_payload_bytes = 5 * 1024 * 1024

    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", "0"))
        if content_length <= 0 or content_length > self.max_payload_bytes:
            self._send_json(413, {"error": "payload_too_large"})
            return

        post_data = self.rfile.read(content_length)

        try:
            platform = self._detect_platform()
            if not self._verify_signature(platform, post_data):
                self._send_json(401, {"error": "invalid_signature"})
                return

            payload = json.loads(post_data.decode("utf-8"))
            if self.callback:
                self.callback(platform, payload)

            self._send_json(200, {"status": "received"})
        except Exception as e:
            console.print(f"[red]Webhook Error: {e}[/]")
            self._send_json(500, {"error": "webhook_error"})

    def _detect_platform(self) -> str:
        if self.headers.get("X-GitHub-Event"):
            return "github"
        if self.headers.get("X-Gitlab-Event"):
            return "gitlab"
        return "gitlab"

    def _verify_signature(self, platform: str, body: bytes) -> bool:
        if not self.secret:
            return True

        if platform == "github":
            signature = self.headers.get("X-Hub-Signature-256", "")
            if not signature.startswith("sha256="):
                return False
            expected = "sha256=" + hmac.new(self.secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
            return hmac.compare_digest(signature, expected)

        token = self.headers.get("X-Gitlab-Token", "")
        return hmac.compare_digest(token, self.secret)

    def _send_json(self, status: int, payload: dict[str, Any]) -> None:
        data = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, format, *args):
        # Suppress default logging
        pass


class CIWebhookManager:
    """Manages the lifecycle of the webhook server."""

    def __init__(self, port: int = 9999, secret: str | None = None):
        self.port = port
        self.secret = secret or os.getenv("RIGOR_WEBHOOK_SECRET")
        self.server = None
        self.thread = None

    def start(self, callback: Callable[[str, dict[str, Any]], None]):
        """Start webhook server in background thread."""
        WebhookHandler.callback = callback
        WebhookHandler.secret = self.secret

        self.server = ReusableTCPServer(("", self.port), WebhookHandler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        console.print(f"[green]🔌 CI Webhook listener started on port {self.port}[/]")
        if not self.secret:
            console.print("[yellow]⚠️  No webhook secret configured. Set RIGOR_WEBHOOK_SECRET in production.[/]")

    def stop(self):
        if self.server:
            self.server.shutdown()
            self.server.server_close()
            console.print("[yellow]Webhook listener stopped[/]")


def parse_github_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Parse GitHub Check Run or Status payload."""
    result = {
        "platform": "github",
        "repo": payload.get("repository", {}).get("full_name", ""),
        "status": payload.get("check_run", {}).get("conclusion", "unknown"),
        "name": payload.get("check_run", {}).get("name", ""),
        "url": payload.get("check_run", {}).get("html_url", ""),
        "ref": payload.get("check_run", {}).get("check_suite", {}).get("head_branch", ""),
    }
    return result


def parse_gitlab_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Parse GitLab Pipeline payload."""
    result = {
        "platform": "gitlab",
        "repo": payload.get("project", {}).get("path_with_namespace", ""),
        "status": payload.get("object_attributes", {}).get("status", "unknown"),
        "name": "Pipeline",
        "url": payload.get("object_attributes", {}).get("url", ""),
        "ref": payload.get("object_attributes", {}).get("ref", ""),
    }
    return result
