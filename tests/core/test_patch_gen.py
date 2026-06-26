"""Tests for rigor.core.patch_gen."""

from rigor.core.patch_gen import ErrorParser, PatchGenerator


class TestErrorParser:
    """Test suite for ErrorParser."""

    def test_parse_python_traceback(self):
        """Test parsing Python traceback errors."""
        error = """Traceback (most recent call last):
  File "/app/test.py", line 42, in test_login
    result = do_something()
NameError: name 'do_something' is not defined"""
        issues = ErrorParser.parse(error)
        assert len(issues) >= 1
        assert any("test.py" in i["file"] and i["line"] == 42 for i in issues)

    def test_parse_pytest_failed(self):
        """Test parsing pytest FAILED output."""
        error = "FAILED tests/test_auth.py::test_login - AssertionError: Expected 200, got 500"
        issues = ErrorParser.parse(error)
        # Note: pytest output doesn't include line numbers, so file is extracted but line defaults
        assert len(issues) >= 1
        assert any("test_auth.py" in i["file"] for i in issues)

    def test_parse_ruff_error(self):
        """Test parsing ruff lint output."""
        error = "src/main.py:5:8: F401 [*] `os` imported but unused"
        issues = ErrorParser.parse(error)
        assert len(issues) >= 1
        assert any("main.py" in i["file"] for i in issues)

    def test_parse_no_issues(self):
        """Test parsing clean output."""
        error = "All tests passed! 🎉"
        issues = ErrorParser.parse(error)
        assert len(issues) == 0

    def test_parse_mixed_output(self):
        """Test parsing mixed output with valid and invalid lines."""
        error = """Running tests...
FAILED src/test_login.py:10:5: TypeError: 'NoneType' object is not callable
All tests done."""
        issues = ErrorParser.parse(error)
        assert len(issues) >= 1
        assert any("test_login.py" in i["file"] and i["line"] == 10 for i in issues)


class TestPatchGenerator:
    """Test suite for PatchGenerator."""

    def test_deterministic_fix_missing_import_os(self, tmp_workspace):
        """Test auto-fixing missing 'os' import."""
        from rigor.core.file_ops import FileOps

        fo = FileOps(str(tmp_workspace))
        pg = PatchGenerator(fo)
        patch = pg._deterministic_fix("src/main.py", 1, "name 'os' is not defined")
        assert patch == "import os"

    def test_deterministic_fix_missing_import_json(self, tmp_workspace):
        """Test auto-fixing missing 'json' import."""
        from rigor.core.file_ops import FileOps

        fo = FileOps(str(tmp_workspace))
        pg = PatchGenerator(fo)
        patch = pg._deterministic_fix("src/main.py", 1, "name 'json' is not defined")
        assert patch == "import json"

    def test_deterministic_fix_missing_import_path(self, tmp_workspace):
        """Test auto-fixing missing 'Path' import."""
        from rigor.core.file_ops import FileOps

        fo = FileOps(str(tmp_workspace))
        pg = PatchGenerator(fo)
        patch = pg._deterministic_fix("src/main.py", 1, "name 'Path' is not defined")
        assert patch is not None and "pathlib" in patch

    def test_deterministic_fix_unknown_name(self, tmp_workspace):
        """Test that unknown names return None."""
        from rigor.core.file_ops import FileOps

        fo = FileOps(str(tmp_workspace))
        pg = PatchGenerator(fo)
        patch = pg._deterministic_fix("src/main.py", 1, "name 'my_custom_class' is not defined")
        assert patch is None
