"""CI/CD Webhook Listener for Rigor."""

import json
import http.server
import socketserver
import threading
from typing import Callable, Dict, Any
from rich.console import Console

console = Console()


class WebhookHandler(http.server.BaseHTTPRequestHandler):
    """Handles incoming CI/CD webhooks."""
    callback: Callable[[str, Dict[str, Any]], None] = None

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        
        try:
            payload = json.loads(post_data.decode('utf-8'))
            # Determine platform based on headers
            platform = self.headers.get('X-GitHub-Event', 'gitlab')
            if platform != 'gitlab':
                platform = 'github'
                
            if self.callback:
                self.callback(platform, payload)
                
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'{"status": "received"}')
        except Exception as e:
            console.print(f"[red]Webhook Error: {e}[/]")
            self.send_response(500)
            self.end_headers()

    def log_message(self, format, *args):
        # Suppress default logging
        pass


class CIWebhookManager:
    """Manages the lifecycle of the webhook server."""
    
    def __init__(self, port: int = 9999):
        self.port = port
        self.server = None
        self.thread = None
        
    def start(self, callback: Callable[[str, Dict[str, Any]], None]):
        """Start webhook server in background thread."""
        WebhookHandler.callback = callback
        
        with socketserver.TCPServer(("", self.port), WebhookHandler) as self.server:
            self.thread = threading.Thread(target=self.server.serve_forever)
            self.thread.daemon = True
            self.thread.start()
            console.print(f"[green]🔌 CI Webhook listener started on port {self.port}[/]")
            
    def stop(self):
        if self.server:
            self.server.shutdown()
            console.print("[yellow]Webhook listener stopped[/]")


def parse_github_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
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


def parse_gitlab_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
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
