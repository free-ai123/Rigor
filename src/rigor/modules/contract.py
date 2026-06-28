"""Contract checks for API specs, backend routes, frontend calls, and live smoke."""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import requests
import yaml

HTTP_METHODS = {"get", "post", "put", "patch", "delete"}
FRONTEND_EXTENSIONS = {".js", ".jsx", ".ts", ".tsx", ".vue", ".svelte"}
BACKEND_EXTENSIONS = {".py", ".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs"}
SKIP_DIRS = {
    ".git",
    ".hg",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "build",
    "coverage",
    "dist",
    "node_modules",
    "__pycache__",
}


@dataclass(frozen=True)
class Endpoint:
    method: str
    path: str
    source: str
    required_response_fields: frozenset[str] = frozenset()
    request_schema: dict[str, Any] | None = None

    @property
    def key(self) -> tuple[str, str]:
        return self.method, normalize_path(self.path)


@dataclass(frozen=True)
class ApiUsage:
    method: str
    path: str
    file: str
    line: int
    kind: str

    @property
    def key(self) -> tuple[str, str]:
        return self.method, normalize_path(self.path)


@dataclass(frozen=True)
class Finding:
    code: str
    severity: str
    message: str
    file: str | None = None
    line: int | None = None


@dataclass
class ContractReport:
    spec_endpoints: list[Endpoint]
    backend_routes: list[ApiUsage]
    frontend_calls: list[ApiUsage]
    findings: list[Finding]
    live_checks: int = 0
    live_skipped: int = 0

    @property
    def failed(self) -> bool:
        return any(f.severity in {"critical", "high"} for f in self.findings)


def normalize_path(path: str) -> str:
    """Normalize route variables so different frameworks can be compared."""
    cleaned = str(path or "").strip()
    if not cleaned:
        return "/"
    cleaned = re.sub(r"^https?://[^/]+", "", cleaned)
    cleaned = cleaned.split("?", 1)[0].split("#", 1)[0]
    cleaned = re.sub(r"\$\{[^}]+\}", "{param}", cleaned)
    cleaned = re.sub(r"\{[^}/]+\}", "{param}", cleaned)
    cleaned = re.sub(r"<[^>/]+>", "{param}", cleaned)
    cleaned = re.sub(r":([A-Za-z_][A-Za-z0-9_]*)", "{param}", cleaned)
    if not cleaned.startswith("/"):
        cleaned = "/" + cleaned
    cleaned = re.sub(r"/+", "/", cleaned)
    if len(cleaned) > 1:
        cleaned = cleaned.rstrip("/")
    return cleaned


def load_openapi_spec(spec_path: str | os.PathLike[str]) -> dict[str, Any]:
    path = Path(spec_path)
    with path.open(encoding="utf-8") as fh:
        if path.suffix.lower() in {".yaml", ".yml"}:
            return yaml.safe_load(fh) or {}
        return json.load(fh)


def parse_openapi_endpoints(spec_path: str | os.PathLike[str]) -> list[Endpoint]:
    spec = load_openapi_spec(spec_path)
    endpoints: list[Endpoint] = []
    for path, path_item in (spec.get("paths") or {}).items():
        if not isinstance(path_item, dict):
            continue
        for method, operation in path_item.items():
            method_lower = str(method).lower()
            if method_lower not in HTTP_METHODS or not isinstance(operation, dict):
                continue
            response_schema = _success_response_schema(operation, spec)
            required_fields = _required_object_fields(response_schema, spec)
            request_schema = _request_body_schema(operation, spec)
            endpoints.append(
                Endpoint(
                    method=method_lower.upper(),
                    path=path,
                    source=str(spec_path),
                    required_response_fields=frozenset(required_fields),
                    request_schema=request_schema,
                )
            )
    return endpoints


def scan_frontend_calls(frontend_dir: str | os.PathLike[str]) -> list[ApiUsage]:
    calls: list[ApiUsage] = []
    for file_path in _iter_files(frontend_dir, FRONTEND_EXTENSIONS):
        text = _read_text(file_path)
        if not text:
            continue
        calls.extend(_scan_frontend_text(text, file_path))
    return calls


def scan_backend_routes(backend_dir: str | os.PathLike[str]) -> list[ApiUsage]:
    routes: list[ApiUsage] = []
    for file_path in _iter_files(backend_dir, BACKEND_EXTENSIONS):
        text = _read_text(file_path)
        if not text:
            continue
        routes.extend(_scan_backend_text(text, file_path))
    return routes


def check_contract(
    *,
    spec_path: str,
    frontend_dir: str | None = None,
    backend_dir: str | None = None,
    base_url: str | None = None,
    include_unsafe: bool = False,
    forbid_manual_api: bool = False,
    fail_on_extra_backend_routes: bool = False,
    timeout: float = 5.0,
) -> ContractReport:
    spec_endpoints = parse_openapi_endpoints(spec_path)
    spec_keys = {endpoint.key for endpoint in spec_endpoints}
    findings: list[Finding] = []

    if not spec_endpoints:
        findings.append(Finding("spec.empty", "high", f"No OpenAPI paths found in {spec_path}"))

    frontend_calls: list[ApiUsage] = []
    if frontend_dir:
        frontend_calls = scan_frontend_calls(frontend_dir)
        for call in frontend_calls:
            if forbid_manual_api:
                findings.append(
                    Finding(
                        "frontend.manual_api_call",
                        "high",
                        f"Manual API call found: {call.method} {call.path}. Use the generated OpenAPI client.",
                        call.file,
                        call.line,
                    )
                )
            if call.key not in spec_keys:
                findings.append(
                    Finding(
                        "frontend.unknown_endpoint",
                        "high",
                        f"Frontend calls {call.method} {call.path}, but it is not declared in the OpenAPI spec.",
                        call.file,
                        call.line,
                    )
                )

    backend_routes: list[ApiUsage] = []
    if backend_dir:
        backend_routes = scan_backend_routes(backend_dir)
        backend_keys = {route.key for route in backend_routes}
        for endpoint in spec_endpoints:
            if endpoint.key not in backend_keys:
                findings.append(
                    Finding(
                        "backend.missing_route",
                        "high",
                        f"OpenAPI declares {endpoint.method} {endpoint.path}, but no matching backend route was found.",
                    )
                )
        for route in backend_routes:
            if route.key not in spec_keys:
                severity = "high" if fail_on_extra_backend_routes else "medium"
                findings.append(
                    Finding(
                        "backend.undocumented_route",
                        severity,
                        f"Backend implements {route.method} {route.path}, but it is not declared in the OpenAPI spec.",
                        route.file,
                        route.line,
                    )
                )

    live_checks = 0
    live_skipped = 0
    if base_url:
        live_findings, live_checks, live_skipped = _run_live_smoke(
            endpoints=spec_endpoints,
            base_url=base_url,
            include_unsafe=include_unsafe,
            timeout=timeout,
        )
        findings.extend(live_findings)

    return ContractReport(
        spec_endpoints=spec_endpoints,
        backend_routes=backend_routes,
        frontend_calls=frontend_calls,
        findings=findings,
        live_checks=live_checks,
        live_skipped=live_skipped,
    )


def format_contract_report(report: ContractReport) -> str:
    status = "FAIL" if report.failed else "PASS"
    lines = [
        f"# Rigor Contract Check: {status}",
        "",
        "## Summary",
        f"- Spec endpoints: {len(report.spec_endpoints)}",
        f"- Backend routes detected: {len(report.backend_routes)}",
        f"- Frontend API calls detected: {len(report.frontend_calls)}",
        f"- Live checks: {report.live_checks}",
        f"- Live checks skipped: {report.live_skipped}",
        f"- Findings: {len(report.findings)}",
        "",
    ]

    if report.findings:
        lines.append("## Findings")
        for finding in report.findings:
            location = ""
            if finding.file:
                location = f" ({finding.file}"
                if finding.line:
                    location += f":{finding.line}"
                location += ")"
            lines.append(f"- [{finding.severity.upper()}] {finding.code}: {finding.message}{location}")
        lines.append("")

    if report.spec_endpoints:
        lines.append("## Spec Endpoints")
        for endpoint in sorted(report.spec_endpoints, key=lambda e: e.key):
            fields = ""
            if endpoint.required_response_fields:
                fields = f" required={','.join(sorted(endpoint.required_response_fields))}"
            lines.append(f"- {endpoint.method} {endpoint.path}{fields}")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def _iter_files(root: str | os.PathLike[str], extensions: set[str]) -> list[Path]:
    base = Path(root)
    if not base.exists():
        return []
    if base.is_file():
        return [base] if base.suffix.lower() in extensions else []

    files: list[Path] = []
    for path in base.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix.lower() not in extensions:
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        files.append(path)
    return files


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""


def _line_number(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def _scan_frontend_text(text: str, file_path: Path) -> list[ApiUsage]:
    calls: list[ApiUsage] = []
    path_literal = r"[\"'`](?P<path>/(?:api/)?[^\"'`\s]+)[\"'`]"

    for match in re.finditer(rf"\bfetch\s*\(\s*{path_literal}", text, re.DOTALL):
        span = text[match.end() : match.end() + 300]
        method = _method_from_options(span) or "GET"
        calls.append(
            ApiUsage(method.upper(), match.group("path"), str(file_path), _line_number(text, match.start()), "fetch")
        )

    for match in re.finditer(rf"\baxios\.(?P<method>get|post|put|patch|delete)\s*\(\s*{path_literal}", text):
        calls.append(
            ApiUsage(
                match.group("method").upper(),
                match.group("path"),
                str(file_path),
                _line_number(text, match.start()),
                "axios",
            )
        )

    for match in re.finditer(
        rf"\b(?:api|client|http)\.(?P<method>get|post|put|patch|delete)\s*\(\s*{path_literal}", text
    ):
        calls.append(
            ApiUsage(
                match.group("method").upper(),
                match.group("path"),
                str(file_path),
                _line_number(text, match.start()),
                "client",
            )
        )

    for match in re.finditer(
        r"\b(?:axios|request|api|client)\s*\(\s*\{(?P<body>.{0,600}?)\}\s*\)",
        text,
        re.DOTALL,
    ):
        body = match.group("body")
        url_match = re.search(rf"\b(?:url|path)\s*:\s*{path_literal}", body)
        if not url_match:
            continue
        method_match = re.search(r"\bmethod\s*:\s*([\"'`])(?P<method>GET|POST|PUT|PATCH|DELETE)\1", body, re.I)
        method = method_match.group("method").upper() if method_match else "GET"
        calls.append(
            ApiUsage(method, url_match.group("path"), str(file_path), _line_number(text, match.start()), "request")
        )

    return _dedupe_usages(calls)


def _method_from_options(text: str) -> str | None:
    match = re.search(r"\bmethod\s*:\s*([\"'`])(?P<method>GET|POST|PUT|PATCH|DELETE)\1", text, re.I)
    return match.group("method").upper() if match else None


def _scan_backend_text(text: str, file_path: Path) -> list[ApiUsage]:
    routes: list[ApiUsage] = []
    path_literal = r"[\"'`](?P<path>/[^\"'`\s]+)[\"'`]"

    decorator_pattern = rf"@[\w.]+?\.(?P<method>get|post|put|patch|delete)\s*\(\s*{path_literal}"
    for match in re.finditer(decorator_pattern, text):
        routes.append(
            ApiUsage(
                match.group("method").upper(),
                match.group("path"),
                str(file_path),
                _line_number(text, match.start()),
                "python-decorator",
            )
        )

    flask_route_pattern = rf"@[\w.]+?\.route\s*\(\s*{path_literal}(?P<args>.{{0,300}}?)\)"
    for match in re.finditer(flask_route_pattern, text, re.DOTALL):
        methods = re.findall(r"['\"](GET|POST|PUT|PATCH|DELETE)['\"]", match.group("args"), re.I)
        if not methods:
            methods = ["GET"]
        for method in methods:
            routes.append(
                ApiUsage(
                    method.upper(),
                    match.group("path"),
                    str(file_path),
                    _line_number(text, match.start()),
                    "flask-route",
                )
            )

    js_route_pattern = rf"\b(?:app|router)\.(?P<method>get|post|put|patch|delete)\s*\(\s*{path_literal}"
    for match in re.finditer(js_route_pattern, text):
        routes.append(
            ApiUsage(
                match.group("method").upper(),
                match.group("path"),
                str(file_path),
                _line_number(text, match.start()),
                "js-route",
            )
        )

    return _dedupe_usages(routes)


def _dedupe_usages(usages: list[ApiUsage]) -> list[ApiUsage]:
    seen: set[tuple[str, str, str, int]] = set()
    deduped: list[ApiUsage] = []
    for usage in usages:
        key = (usage.method, usage.path, usage.file, usage.line)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(usage)
    return deduped


def _resolve_ref(schema: Any, spec: dict[str, Any]) -> Any:
    if not isinstance(schema, dict) or "$ref" not in schema:
        return schema
    ref = str(schema["$ref"])
    if not ref.startswith("#/"):
        return schema
    current: Any = spec
    for part in ref[2:].split("/"):
        if not isinstance(current, dict):
            return schema
        current = current.get(part)
    return current if current is not None else schema


def _success_response_schema(operation: dict[str, Any], spec: dict[str, Any]) -> dict[str, Any]:
    responses = operation.get("responses") or {}
    response = None
    for status_code in ("200", "201", "202", "204"):
        response = responses.get(status_code)
        if response:
            break
    if not isinstance(response, dict):
        return {}
    content = response.get("content") or {}
    for media in ("application/json", "application/problem+json"):
        schema = (content.get(media) or {}).get("schema")
        if schema:
            resolved = _resolve_ref(schema, spec)
            return resolved if isinstance(resolved, dict) else {}
    for media_info in content.values():
        schema = media_info.get("schema") if isinstance(media_info, dict) else None
        if schema:
            resolved = _resolve_ref(schema, spec)
            return resolved if isinstance(resolved, dict) else {}
    return {}


def _request_body_schema(operation: dict[str, Any], spec: dict[str, Any]) -> dict[str, Any] | None:
    body = operation.get("requestBody") or {}
    if not isinstance(body, dict):
        return None
    content = body.get("content") or {}
    for media in ("application/json", "application/x-www-form-urlencoded"):
        schema = (content.get(media) or {}).get("schema")
        if schema:
            resolved = _resolve_ref(schema, spec)
            return resolved if isinstance(resolved, dict) else None
    return None


def _required_object_fields(schema: dict[str, Any], spec: dict[str, Any]) -> set[str]:
    schema = _resolve_ref(schema, spec)
    if not isinstance(schema, dict):
        return set()
    if schema.get("type") == "array":
        schema = _resolve_ref(schema.get("items") or {}, spec)
    if not isinstance(schema, dict) or schema.get("type") != "object":
        return set()
    fields = set(schema.get("required") or [])
    if not fields:
        fields = set((schema.get("properties") or {}).keys())
    return {str(field) for field in fields}


def _run_live_smoke(
    *,
    endpoints: list[Endpoint],
    base_url: str,
    include_unsafe: bool,
    timeout: float,
) -> tuple[list[Finding], int, int]:
    findings: list[Finding] = []
    checked = 0
    skipped = 0
    base = base_url.rstrip("/")

    for endpoint in endpoints:
        if endpoint.method != "GET" and not include_unsafe:
            skipped += 1
            continue
        if "{param}" in normalize_path(endpoint.path):
            skipped += 1
            continue

        checked += 1
        url = f"{base}{endpoint.path}"
        try:
            response = requests.request(
                endpoint.method,
                url,
                json=_sample_from_schema(endpoint.request_schema) if endpoint.request_schema else None,
                timeout=timeout,
                headers={"Accept": "application/json"},
            )
        except requests.RequestException as exc:
            findings.append(Finding("live.request_failed", "high", f"{endpoint.method} {endpoint.path} failed: {exc}"))
            continue

        if response.status_code in {401, 403}:
            findings.append(
                Finding(
                    "live.auth_required",
                    "medium",
                    f"{endpoint.method} {endpoint.path} is reachable but requires auth ({response.status_code}).",
                )
            )
            continue
        if response.status_code in {404, 405}:
            findings.append(
                Finding(
                    "live.route_missing",
                    "high",
                    f"{endpoint.method} {endpoint.path} returned {response.status_code}; route may be missing or method mismatched.",
                )
            )
            continue
        if response.status_code >= 500:
            findings.append(
                Finding(
                    "live.server_error",
                    "high",
                    f"{endpoint.method} {endpoint.path} returned server error {response.status_code}.",
                )
            )
            continue
        if response.status_code >= 400:
            findings.append(
                Finding(
                    "live.client_error",
                    "medium",
                    f"{endpoint.method} {endpoint.path} returned {response.status_code}.",
                )
            )
            continue

        missing = _missing_response_fields(response, endpoint.required_response_fields)
        if missing:
            findings.append(
                Finding(
                    "live.response_shape_mismatch",
                    "high",
                    f"{endpoint.method} {endpoint.path} missing response fields: {', '.join(sorted(missing))}.",
                )
            )

    return findings, checked, skipped


def _missing_response_fields(response: requests.Response, required_fields: frozenset[str]) -> set[str]:
    if not required_fields:
        return set()
    content_type = response.headers.get("content-type", "")
    if "json" not in content_type.lower():
        return set(required_fields)
    try:
        payload = response.json()
    except ValueError:
        return set(required_fields)
    if isinstance(payload, list):
        payload = payload[0] if payload else {}
    if not isinstance(payload, dict):
        return set(required_fields)
    return set(required_fields) - set(payload.keys())


def _sample_from_schema(schema: dict[str, Any] | None, depth: int = 0) -> Any:
    if not schema or depth > 4:
        return None
    schema_type = schema.get("type", "object")
    if schema_type == "object":
        result: dict[str, Any] = {}
        for name, prop_schema in (schema.get("properties") or {}).items():
            result[name] = _sample_from_schema(prop_schema, depth + 1)
        return result
    if schema_type == "array":
        return [_sample_from_schema(schema.get("items") or {}, depth + 1)]
    if schema_type == "integer":
        return schema.get("example", schema.get("default", 1))
    if schema_type == "number":
        return schema.get("example", schema.get("default", 1.0))
    if schema_type == "boolean":
        return schema.get("example", schema.get("default", True))
    return schema.get("example", schema.get("default", "string"))
