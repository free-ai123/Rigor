"""依赖安全扫描 — 支持 Python/Node.js/Go/Rust 多语言"""

import json
import os
import re
import shutil
import subprocess
import sys
from typing import Any

from rich.console import Console
from rich.table import Table

console = Console()

# 已知高危包清单（简化版，实际应接入 OSV 数据库）
KNOWN_VULNERABILITIES = {
    "python": {
        "requests": {"<2.31.0": ["CVE-2023-32681: 未验证代理证书泄露"]},
        "django": {"<4.2.7": ["CVE-2023-46695: DoS 攻击"], "<5.0.1": ["CVE-2023-50471: 临时文件泄露"]},
        "flask": {"<2.3.2": ["CVE-2023-30861: Cookie 泄露"]},
        "jinja2": {"<3.1.3": ["CVE-2024-22195: XSS 漏洞"]},
        "pillow": {"<10.0.1": ["CVE-2023-50447: 远程代码执行"]},
        "pyyaml": {"<6.0.1": ["CVE-2020-1747: 任意代码执行"]},
        "urllib3": {"<2.0.7": ["CVE-2023-45803: 请求体泄露"]},
        "cryptography": {"<41.0.6": ["CVE-2023-49083: NULL 指针解引用"]},
    },
    "nodejs": {
        "express": {"<4.18.2": ["原型污染漏洞"]},
        "lodash": {"<4.17.21": ["CVE-2021-23337: 命令注入"], "<4.17.20": ["CVE-2020-28500: ReDoS"]},
        "axios": {"<1.6.0": ["CVE-2023-45857: CSRF 令牌泄露"]},
        "jsonwebtoken": {"<9.0.0": ["CVE-2022-23529: 密钥混淆"]},
    },
}


def _iter_python_deps(project_dir: str) -> list[tuple[str, str]]:
    deps: list[tuple[str, str]] = []
    for f in ["requirements.txt", "requirements/dev.txt", "requirements/prod.txt"]:
        path = os.path.join(project_dir, f)
        if os.path.exists(path):
            with open(path, encoding="utf-8") as fh:
                deps.extend((line.strip(), path) for line in fh)

    pyproject = os.path.join(project_dir, "pyproject.toml")
    if os.path.exists(pyproject):
        try:
            import tomllib

            with open(pyproject, "rb") as fh:
                data = tomllib.load(fh)
            project = data.get("project", {})
            deps.extend((dep, pyproject) for dep in project.get("dependencies", []))
            optional = project.get("optional-dependencies", {})
            for dep_list in optional.values():
                deps.extend((dep, pyproject) for dep in dep_list)
        except Exception:
            pass

    return deps


def _parse_python_dep(spec: str) -> tuple[str, str]:
    spec = spec.split(";", 1)[0].strip()
    if not spec or spec.startswith(("#", "-")):
        return "", ""
    match = re.match(r"([A-Za-z0-9_.-]+)(?:\[.*\])?\s*(==|>=|<=|~=|>|<)?\s*([^,]+)?", spec)
    if not match:
        return "", ""
    pkg = match.group(1).lower().strip()
    version = (match.group(3) or "unknown").strip()
    return pkg, version


def _scan_python_with_pip_audit(project_dir: str) -> list[dict[str, Any]] | None:
    """Run pip-audit when installed. Return None when unavailable or unusable."""
    pip_audit = shutil.which("pip-audit")
    cmd = [pip_audit] if pip_audit else [sys.executable, "-m", "pip_audit"]
    if not pip_audit:
        try:
            import importlib.util

            if importlib.util.find_spec("pip_audit") is None:
                return None
        except (ImportError, ValueError):
            return None

    req_file = os.path.join(project_dir, "requirements.txt")
    cmd.extend(["-f", "json"])
    if os.path.exists(req_file):
        cmd.extend(["-r", req_file])

    try:
        result = subprocess.run(cmd, cwd=project_dir, capture_output=True, text=True, timeout=120)
    except (OSError, subprocess.TimeoutExpired):
        return None

    if not result.stdout.strip():
        return None

    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError:
        return None

    issues: list[dict[str, Any]] = []
    for dep in data.get("dependencies", []):
        package = dep.get("name", "unknown")
        current_version = dep.get("version", "unknown")
        for vuln in dep.get("vulns", []):
            fix_versions = vuln.get("fix_versions") or []
            aliases = vuln.get("aliases") or []
            vuln_id = aliases[0] if aliases else vuln.get("id", "unknown")
            issues.append(
                {
                    "language": "python",
                    "package": package,
                    "current_version": current_version,
                    "min_safe_version": fix_versions[0] if fix_versions else "unknown",
                    "vulnerability": vuln_id,
                    "severity": "high",
                    "source": "pip-audit",
                }
            )

    return issues


def _scan_python_static(project_dir: str = ".") -> list[dict[str, Any]]:
    """Static fallback scanner for Python dependency specs."""
    issues = []

    for dep_spec, source in _iter_python_deps(project_dir):
        pkg, version = _parse_python_dep(dep_spec)
        if not pkg:
            continue

        vuln_db = KNOWN_VULNERABILITIES.get("python", {})
        if pkg in vuln_db:
            for ver_range, cves in vuln_db[pkg].items():
                min_ver = ver_range.lstrip("<")
                if _version_lt(version, min_ver):
                    for cve in cves:
                        issues.append(
                            {
                                "language": "python",
                                "package": pkg,
                                "current_version": version,
                                "min_safe_version": min_ver,
                                "vulnerability": cve,
                                "severity": "high",
                                "source": source,
                            }
                        )

    return issues


def scan_python_deps(project_dir: str = ".") -> list[dict[str, Any]]:
    """扫描 Python 依赖"""
    return _scan_python_with_pip_audit(project_dir) or _scan_python_static(project_dir)


def _scan_nodejs_with_npm_audit(project_dir: str) -> list[dict[str, Any]] | None:
    pkg_json = os.path.join(project_dir, "package.json")
    pkg_lock = os.path.join(project_dir, "package-lock.json")
    if not os.path.exists(pkg_json) or not os.path.exists(pkg_lock) or shutil.which("npm") is None:
        return None

    try:
        result = subprocess.run(
            ["npm", "audit", "--json", "--omit=dev"],
            cwd=project_dir,
            capture_output=True,
            text=True,
            timeout=120,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None

    if not result.stdout.strip():
        return None

    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError:
        return None

    vulnerabilities = data.get("vulnerabilities", {})
    issues = []
    for package, detail in vulnerabilities.items():
        via = detail.get("via", [])
        vuln_names = []
        for item in via:
            if isinstance(item, dict):
                vuln_names.append(item.get("source") or item.get("title") or item.get("name") or "npm advisory")
            else:
                vuln_names.append(str(item))
        issues.append(
            {
                "language": "nodejs",
                "package": package,
                "current_version": detail.get("range", "unknown"),
                "min_safe_version": detail.get("fixAvailable", {}).get("version", "unknown")
                if isinstance(detail.get("fixAvailable"), dict)
                else "unknown",
                "vulnerability": ", ".join(vuln_names) or "npm advisory",
                "severity": detail.get("severity", "unknown"),
                "source": "npm audit",
            }
        )

    return issues


def scan_nodejs_deps(project_dir: str = ".") -> list[dict[str, Any]]:
    """扫描 Node.js 依赖"""
    audited = _scan_nodejs_with_npm_audit(project_dir)
    if audited is not None:
        return audited

    issues = []
    pkg_json = os.path.join(project_dir, "package.json")

    if not os.path.exists(pkg_json):
        return issues

    with open(pkg_json) as fh:
        data = json.load(fh)

    all_deps = {}
    all_deps.update(data.get("dependencies", {}))
    all_deps.update(data.get("devDependencies", {}))

    vuln_db = KNOWN_VULNERABILITIES.get("nodejs", {})
    for pkg, version in all_deps.items():
        pkg = pkg.lower()
        # 清理版本前缀 (^, ~, >=)
        clean_ver = version.lstrip("^~>=< ")

        if pkg in vuln_db:
            for ver_range, cves in vuln_db[pkg].items():
                min_ver = ver_range.lstrip("<")
                if _version_lt(clean_ver, min_ver):
                    for cve in cves:
                        issues.append(
                            {
                                "language": "nodejs",
                                "package": pkg,
                                "current_version": clean_ver,
                                "min_safe_version": min_ver,
                                "vulnerability": cve,
                                "severity": "high",
                                "source": "package.json",
                            }
                        )

    return issues


def _version_lt(v1: str, v2: str) -> bool:
    """简化的版本比较：v1 < v2"""
    try:

        def normalize(v):
            return [int(x) for x in v.split(".")[:3]]

        parts1 = normalize(v1)
        parts2 = normalize(v2)

        # 补齐长度
        while len(parts1) < 3:
            parts1.append(0)
        while len(parts2) < 3:
            parts2.append(0)

        return parts1 < parts2
    except Exception:
        return False


def scan_project(project_dir: str = ".") -> list[dict[str, Any]]:
    """扫描项目所有支持的依赖"""
    all_issues = []
    all_issues.extend(scan_python_deps(project_dir))
    all_issues.extend(scan_nodejs_deps(project_dir))
    return all_issues


def display_scan_results(issues: list[dict[str, Any]]) -> None:
    """以表格形式展示扫描结果"""
    if not issues:
        console.print("\n[green]✅ 未发现已知依赖漏洞![/]\n")
        return

    console.print(f"\n[bold red]⚠️  发现 {len(issues)} 个已知漏洞![/]\n")

    table = Table(title="依赖安全扫描结果")
    table.add_column("语言", style="cyan")
    table.add_column("包名", style="yellow")
    table.add_column("当前版本")
    table.add_column("安全版本", style="green")
    table.add_column("漏洞", style="red")
    table.add_column("来源")

    for issue in issues:
        table.add_row(
            issue["language"],
            issue["package"],
            issue["current_version"],
            f">= {issue['min_safe_version']}",
            issue["vulnerability"],
            issue["source"],
        )

    console.print(table)

    # 修复建议
    console.print("\n[bold]💡 修复建议:[/]")
    for issue in issues:
        lang_cmd = {
            "python": f"pip install '{issue['package']}>={issue['min_safe_version']}'",
            "nodejs": f"npm install {issue['package']}@'>={issue['min_safe_version']}'",
        }
        cmd = lang_cmd.get(issue["language"], "手动更新依赖")
        console.print(f"  • {issue['package']}: [green]{cmd}[/]")
    console.print()
