"""API Mock 自动生成 — 根据 API spec 生成 Mock Server"""

import json
import os
from typing import Any

from rich.console import Console

console = Console()


def parse_api_spec(spec_path: str) -> list[dict[str, Any]]:
    """解析 API 规格文件（支持 OpenAPI JSON/YAML）"""
    if not os.path.exists(spec_path):
        console.print(f"[red]❌ 找不到 API spec: {spec_path}[/]")
        return []

    with open(spec_path) as f:
        if spec_path.endswith(".json"):
            spec = json.load(f)
        else:
            # YAML 需要 pyyaml，此处简化处理
            console.print("[yellow]⚠️  YAML 解析需要安装 pyyaml，尝试 JSON 格式[/]")
            return []

    endpoints = []
    paths = spec.get("paths", {})

    for path, methods in paths.items():
        for method, details in methods.items():
            if method not in ("get", "post", "put", "delete", "patch"):
                continue

            responses = details.get("responses", {})
            success_response = responses.get("200") or responses.get("201") or {}
            content = success_response.get("content", {})

            # 生成 mock 数据
            mock_data = {}
            for media_type, schema_info in content.items():
                schema = schema_info.get("schema", {})
                mock_data = _generate_mock_from_schema(schema)

            endpoints.append(
                {
                    "path": path,
                    "method": method.upper(),
                    "summary": details.get("summary", ""),
                    "mock_data": mock_data,
                    "status_code": 200 if method == "get" else 201,
                }
            )

    return endpoints


def _generate_mock_from_schema(schema: dict[str, Any], depth: int = 0) -> Any:
    """根据 JSON Schema 生成 Mock 数据"""
    if depth > 3:  # 防止无限递归
        return None

    schema_type = schema.get("type", "string")

    if schema_type == "object":
        properties = schema.get("properties", {})
        result = {}
        for prop_name, prop_schema in properties.items():
            result[prop_name] = _generate_mock_from_schema(prop_schema, depth + 1)
        return result

    elif schema_type == "array":
        items = schema.get("items", {})
        return [_generate_mock_from_schema(items, depth + 1)]

    elif schema_type == "string":
        if "format" in schema:
            fmt = schema["format"]
            if fmt == "date-time":
                return "2026-06-26T12:00:00Z"
            elif fmt == "email":
                return "user@example.com"
            elif fmt == "uri":
                return "https://example.com"
        example = schema.get("example")
        if example:
            return example
        return schema.get("default", "string")

    elif schema_type == "integer":
        return schema.get("example", schema.get("default", 42))

    elif schema_type == "number":
        return schema.get("example", schema.get("default", 3.14))

    elif schema_type == "boolean":
        return schema.get("example", schema.get("default", True))

    return None


def generate_mock_server(spec_path: str, output_dir: str = "./mock-server", framework: str = "flask") -> str:
    """生成 Mock Server 代码"""

    endpoints = parse_api_spec(spec_path)
    if not endpoints:
        console.print("[red]❌ 无法解析 API spec[/]")
        return ""

    os.makedirs(output_dir, exist_ok=True)

    if framework == "flask":
        code = _generate_flask_mock(endpoints)
    elif framework == "fastapi":
        code = _generate_fastapi_mock(endpoints)
    else:
        code = _generate_flask_mock(endpoints)

    output_file = os.path.join(output_dir, "mock_server.py")
    with open(output_file, "w") as f:
        f.write(code)

    # 生成 requirements.txt
    req_file = os.path.join(output_dir, "requirements.txt")
    with open(req_file, "w") as f:
        f.write("flask>=2.3\n" if framework == "flask" else "fastapi>=0.100\nuvicorn>=0.23\n")

    console.print("\n[green]✅ Mock Server 已生成![/]")
    console.print(f"  目录: {output_dir}")
    console.print(f"  端点: {len(endpoints)} 个")
    console.print(f"  启动: python {output_file}\n")

    return output_file


def _generate_flask_mock(endpoints: list[dict[str, Any]]) -> str:
    """生成 Flask Mock Server"""
    lines = [
        '"""Auto-generated Mock Server — Rigor CLI"""',
        "from flask import Flask, jsonify",
        "",
        "app = Flask(__name__)",
        "",
    ]

    for ep in endpoints:
        method = ep["method"].lower()
        path = ep["path"]
        decorator = f'@app.route("{path}", methods=["{ep["method"]}"])'
        func_name = f"mock_{method}_{path.strip('/').replace('/', '_').replace('-', '_')}"

        lines.append(decorator)
        lines.append(f"def {func_name}():")
        lines.append(f'    """{ep["summary"]}"""')
        lines.append(f"    return jsonify({json.dumps(ep['mock_data'], indent=8)}), {ep['status_code']}")
        lines.append("")

    lines.append("")
    lines.append('if __name__ == "__main__":')
    lines.append('    app.run(host="0.0.0.0", port=5000, debug=True)')

    return "\n".join(lines)


def _generate_fastapi_mock(endpoints: list[dict[str, Any]]) -> str:
    """生成 FastAPI Mock Server"""
    lines = [
        '"""Auto-generated Mock Server — Rigor CLI"""',
        "from fastapi import FastAPI",
        "",
        "app = FastAPI(title='Mock API')",
        "",
    ]

    for ep in endpoints:
        method = ep["method"].lower()
        path = ep["path"]
        func_name = f"mock_{method}_{path.strip('/').replace('/', '_').replace('-', '_')}"

        lines.append(f'@app.{method}("{path}")')
        lines.append(f"def {func_name}():")
        lines.append(f'    """{ep["summary"]}"""')
        lines.append(f"    return {json.dumps(ep['mock_data'], indent=8)}")
        lines.append("")

    lines.append("")
    lines.append('if __name__ == "__main__":')
    lines.append("    import uvicorn")
    lines.append('    uvicorn.run(app, host="0.0.0.0", port=8001)')

    return "\n".join(lines)
