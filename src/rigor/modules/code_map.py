"""Lightweight codebase map generation for agent context selection."""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

DEFAULT_EXCLUDES = {
    ".git",
    ".venv",
    "__pycache__",
    "build",
    "dist",
    "htmlcov",
    "node_modules",
}


def _is_excluded(path: Path) -> bool:
    return any(part in DEFAULT_EXCLUDES for part in path.parts)


def _path_priority(path: Path) -> tuple[int, str]:
    first = path.parts[0] if path.parts else ""
    priority = {"src": 0, "tests": 1}.get(first, 2)
    return priority, str(path)


def _symbol_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.AsyncFunctionDef):
        return f"async def {node.name}"
    if isinstance(node, ast.FunctionDef):
        return f"def {node.name}"
    if isinstance(node, ast.ClassDef):
        return f"class {node.name}"
    return None


def _parse_python_file(path: Path, root: Path) -> dict[str, Any]:
    rel = str(path.relative_to(root))
    try:
        content = path.read_text(encoding="utf-8", errors="replace")
        tree = ast.parse(content)
    except SyntaxError as e:
        return {"path": rel, "error": f"syntax error: {e.msg}", "symbols": [], "imports": []}
    except OSError as e:
        return {"path": rel, "error": str(e), "symbols": [], "imports": []}

    symbols = []
    imports = []
    for node in tree.body:
        symbol = _symbol_name(node)
        if symbol:
            symbols.append({"name": symbol, "line": getattr(node, "lineno", 0)})
        elif isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.append(node.module)

    return {
        "path": rel,
        "lines": len(content.splitlines()),
        "symbols": symbols,
        "imports": sorted(set(imports)),
    }


def build_code_map(project_dir: str = ".", max_files: int = 200) -> dict[str, Any]:
    """Build a compact Python code map for the project."""
    root = Path(project_dir).resolve()
    files = []
    candidates = []
    for path in root.rglob("*.py"):
        rel = path.relative_to(root)
        if _is_excluded(rel):
            continue
        candidates.append(path)

    for path in sorted(candidates, key=lambda p: _path_priority(p.relative_to(root))):
        file_info = _parse_python_file(path, root)
        if path.name == "__init__.py" and file_info.get("lines", 0) == 0:
            continue
        files.append(file_info)
        if len(files) >= max_files:
            break

    return {"root": str(root), "file_count": len(files), "files": files}


def format_code_map(code_map: dict[str, Any]) -> str:
    """Render a code map as Markdown."""
    lines = [f"# Code Map ({code_map['file_count']} files)", ""]
    for file_info in code_map["files"]:
        lines.append(f"## `{file_info['path']}`")
        if file_info.get("error"):
            lines.append(f"- Error: {file_info['error']}")
            lines.append("")
            continue
        lines.append(f"- Lines: {file_info.get('lines', 0)}")
        imports = file_info.get("imports", [])
        if imports:
            lines.append(f"- Imports: {', '.join(imports[:8])}")
        symbols = file_info.get("symbols", [])
        if symbols:
            lines.append("- Symbols:")
            for symbol in symbols[:20]:
                lines.append(f"  - L{symbol['line']}: `{symbol['name']}`")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"
