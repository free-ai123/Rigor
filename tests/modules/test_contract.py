import json

from rigor.modules.contract import (
    check_contract,
    format_contract_report,
    normalize_path,
    scan_backend_routes,
    scan_frontend_calls,
)


def write_openapi(tmp_path, paths):
    spec = tmp_path / "openapi.json"
    spec.write_text(
        json.dumps(
            {
                "openapi": "3.0.0",
                "info": {"title": "Example", "version": "1.0.0"},
                "paths": paths,
            }
        ),
        encoding="utf-8",
    )
    return spec


def test_normalize_path_handles_framework_route_params():
    assert normalize_path("/api/v1/users/{id}") == "/api/v1/users/{param}"
    assert normalize_path("/api/v1/users/:id") == "/api/v1/users/{param}"
    assert normalize_path("/api/v1/users/<id>") == "/api/v1/users/{param}"
    assert normalize_path("/api/v1/users/${id}?x=1") == "/api/v1/users/{param}"


def test_contract_check_passes_when_spec_backend_and_frontend_align(tmp_path):
    spec = write_openapi(
        tmp_path,
        {
            "/api/v1/alerts/rules": {
                "get": {
                    "responses": {
                        "200": {
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "required": ["alert_rules"],
                                        "properties": {"alert_rules": {"type": "array"}},
                                    }
                                }
                            }
                        }
                    }
                }
            }
        },
    )
    backend = tmp_path / "backend"
    backend.mkdir()
    (backend / "routes.py").write_text(
        """
from fastapi import APIRouter
router = APIRouter()

@router.get("/api/v1/alerts/rules")
def list_rules():
    return {"alert_rules": []}
""",
        encoding="utf-8",
    )
    frontend = tmp_path / "frontend"
    frontend.mkdir()
    (frontend / "alerts.ts").write_text(
        'export const listRules = () => api.get("/api/v1/alerts/rules");\n',
        encoding="utf-8",
    )

    report = check_contract(spec_path=str(spec), backend_dir=str(backend), frontend_dir=str(frontend))

    assert not report.failed
    assert len(report.findings) == 0
    assert "Rigor Contract Check: PASS" in format_contract_report(report)


def test_contract_check_fails_on_frontend_path_not_in_spec(tmp_path):
    spec = write_openapi(
        tmp_path,
        {
            "/api/v1/alerts/rules": {
                "get": {"responses": {"200": {"content": {"application/json": {"schema": {"type": "object"}}}}}}
            }
        },
    )
    frontend = tmp_path / "frontend"
    frontend.mkdir()
    (frontend / "alerts.ts").write_text('fetch("/api/v1/alert-rules");\n', encoding="utf-8")

    report = check_contract(spec_path=str(spec), frontend_dir=str(frontend))

    assert report.failed
    assert any(f.code == "frontend.unknown_endpoint" for f in report.findings)


def test_contract_check_fails_when_backend_route_missing(tmp_path):
    spec = write_openapi(
        tmp_path,
        {
            "/api/v1/alerts/rules": {
                "post": {"responses": {"201": {"content": {"application/json": {"schema": {"type": "object"}}}}}}
            }
        },
    )
    backend = tmp_path / "backend"
    backend.mkdir()
    (backend / "routes.py").write_text(
        '@router.post("/api/v1/alert-rules")\ndef create_rule():\n    return {}\n',
        encoding="utf-8",
    )

    report = check_contract(spec_path=str(spec), backend_dir=str(backend))

    assert report.failed
    assert any(f.code == "backend.missing_route" for f in report.findings)


def test_scan_backend_routes_detects_flask_and_express(tmp_path):
    backend = tmp_path / "backend"
    backend.mkdir()
    (backend / "app.py").write_text(
        '@app.route("/api/v1/hosts", methods=["GET", "POST"])\ndef hosts():\n    return {}\n',
        encoding="utf-8",
    )
    (backend / "routes.ts").write_text('router.delete("/api/v1/hosts/:id", handler);\n', encoding="utf-8")

    routes = scan_backend_routes(backend)

    assert {route.key for route in routes} == {
        ("GET", "/api/v1/hosts"),
        ("POST", "/api/v1/hosts"),
        ("DELETE", "/api/v1/hosts/{param}"),
    }


def test_scan_frontend_calls_detects_fetch_method_options(tmp_path):
    frontend = tmp_path / "frontend"
    frontend.mkdir()
    (frontend / "api.ts").write_text(
        """
fetch("/api/v1/hosts", { method: "POST", body: JSON.stringify({}) });
axios.delete("/api/v1/hosts/123");
""",
        encoding="utf-8",
    )

    calls = scan_frontend_calls(frontend)

    assert ("POST", "/api/v1/hosts") in {call.key for call in calls}
    assert ("DELETE", "/api/v1/hosts/123") in {call.key for call in calls}
