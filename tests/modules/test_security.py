"""Tests for dependency security scanning."""

import json
import subprocess

from rigor.modules.security import scan_nodejs_deps, scan_python_deps


def test_scan_python_deps_reads_pyproject(tmp_path):
    (tmp_path / "pyproject.toml").write_text(
        """
[project]
dependencies = ["pyyaml>=5.0", "requests>=2.31.0"]
""",
        encoding="utf-8",
    )

    issues = scan_python_deps(str(tmp_path))

    assert any(issue["package"] == "pyyaml" for issue in issues)
    assert not any(issue["package"] == "requests" for issue in issues)


def test_scan_python_deps_uses_pip_audit_json(tmp_path, monkeypatch):
    (tmp_path / "requirements.txt").write_text("demo==1.0.0\n", encoding="utf-8")

    def fake_which(binary):
        return "/usr/bin/pip-audit" if binary == "pip-audit" else None

    def fake_run(*args, **kwargs):
        payload = {
            "dependencies": [
                {
                    "name": "demo",
                    "version": "1.0.0",
                    "vulns": [
                        {
                            "id": "PYSEC-1",
                            "aliases": ["CVE-2099-0001"],
                            "fix_versions": ["1.0.1"],
                        }
                    ],
                }
            ]
        }
        return subprocess.CompletedProcess(args=args[0], returncode=1, stdout=json.dumps(payload), stderr="")

    monkeypatch.setattr("rigor.modules.security.shutil.which", fake_which)
    monkeypatch.setattr("rigor.modules.security.subprocess.run", fake_run)

    issues = scan_python_deps(str(tmp_path))

    assert issues == [
        {
            "language": "python",
            "package": "demo",
            "current_version": "1.0.0",
            "min_safe_version": "1.0.1",
            "vulnerability": "CVE-2099-0001",
            "severity": "high",
            "source": "pip-audit",
        }
    ]


def test_scan_nodejs_deps_uses_npm_audit_json(tmp_path, monkeypatch):
    (tmp_path / "package.json").write_text('{"dependencies":{"demo":"1.0.0"}}', encoding="utf-8")
    (tmp_path / "package-lock.json").write_text("{}", encoding="utf-8")

    def fake_which(binary):
        return "/usr/bin/npm" if binary == "npm" else None

    def fake_run(*args, **kwargs):
        payload = {
            "vulnerabilities": {
                "demo": {
                    "severity": "high",
                    "range": "<1.0.1",
                    "fixAvailable": {"version": "1.0.1"},
                    "via": [{"source": "CVE-2099-0002"}],
                }
            }
        }
        return subprocess.CompletedProcess(args=args[0], returncode=1, stdout=json.dumps(payload), stderr="")

    monkeypatch.setattr("rigor.modules.security.shutil.which", fake_which)
    monkeypatch.setattr("rigor.modules.security.subprocess.run", fake_run)

    issues = scan_nodejs_deps(str(tmp_path))

    assert issues[0]["package"] == "demo"
    assert issues[0]["min_safe_version"] == "1.0.1"
    assert issues[0]["vulnerability"] == "CVE-2099-0002"
    assert issues[0]["source"] == "npm audit"
