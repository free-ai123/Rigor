"""Tests for rigor.core.file_ops."""

import pytest
from rigor.core.file_ops import FileOps


class TestFileOps:
    """Test suite for FileOps class."""

    def test_safe_path_within_workspace(self, tmp_workspace):
        """Test that paths are resolved within workspace."""
        fo = FileOps(str(tmp_workspace))
        p = fo._safe_path("src/main.py")
        assert p.name == "main.py"
        assert p.is_relative_to(tmp_workspace.resolve())

    def test_safe_path_rejects_escape(self, tmp_workspace):
        """Test that paths cannot escape workspace."""
        fo = FileOps(str(tmp_workspace))
        with pytest.raises(PermissionError):
            fo._safe_path("../../etc/passwd")

    def test_read_file(self, tmp_workspace):
        """Test reading a file."""
        fo = FileOps(str(tmp_workspace))
        content = fo.read_file("src/main.py")
        assert "import os" in content
        assert "def hello" in content

    def test_read_file_pagination(self, tmp_workspace):
        """Test reading with offset and limit."""
        fo = FileOps(str(tmp_workspace))
        content = fo.read_file("src/main.py", offset=1, limit=3)
        assert "Lines 1-3" in content

    def test_read_file_not_found(self, tmp_workspace):
        """Test reading non-existent file."""
        fo = FileOps(str(tmp_workspace))
        with pytest.raises(FileNotFoundError):
            fo.read_file("nonexistent.py")

    def test_write_file(self, tmp_workspace):
        """Test writing a file."""
        fo = FileOps(str(tmp_workspace))
        result = fo.write_file("src/new.py", "print('hello')")
        assert "File written" in result
        assert (tmp_workspace / "src" / "new.py").exists()
        assert (tmp_workspace / "src" / "new.py").read_text() == "print('hello')"

    def test_write_file_creates_dirs(self, tmp_workspace):
        """Test that write_file creates parent directories."""
        fo = FileOps(str(tmp_workspace))
        fo.write_file("a/b/c/new.py", "pass")
        assert (tmp_workspace / "a" / "b" / "c" / "new.py").exists()

    def test_patch_file(self, tmp_workspace):
        """Test patching a file."""
        fo = FileOps(str(tmp_workspace))
        result = fo.patch_file(
            "src/main.py", "def hello(name: str) -> str:", "def hello(name: str) -> str:\n    pass\n"
        )
        assert "Patch applied" in result
        content = (tmp_workspace / "src" / "main.py").read_text()
        assert "pass" in content

    def test_patch_file_not_found_string(self, tmp_workspace):
        """Test patching with non-existent string."""
        fo = FileOps(str(tmp_workspace))
        with pytest.raises(ValueError):
            fo.patch_file("src/main.py", "THIS_STRING_DOES_NOT_EXIST", "replacement")

    def test_patch_file_not_found_file(self, tmp_workspace):
        """Test patching non-existent file."""
        fo = FileOps(str(tmp_workspace))
        with pytest.raises(FileNotFoundError):
            fo.patch_file("nonexistent.py", "old", "new")

    def test_search_files_content(self, tmp_workspace):
        """Test searching file content."""
        fo = FileOps(str(tmp_workspace))
        results = fo.search_files("def hello", target="content")
        assert len(results) > 0
        assert "main.py" in results[0]

    def test_search_files_by_glob(self, tmp_workspace):
        """Test finding files by glob."""
        fo = FileOps(str(tmp_workspace))
        results = fo.search_files("*.py", target="files")
        assert len(results) >= 3  # main.py, utils.py, test_main.py, __init__.py

    def test_search_files_limit(self, tmp_workspace):
        """Test search respects limit."""
        fo = FileOps(str(tmp_workspace))
        results = fo.search_files("import", target="content", limit=1)
        assert len(results) == 1

    def test_list_dir(self, tmp_workspace):
        """Test listing directory."""
        fo = FileOps(str(tmp_workspace))
        results = fo.list_dir(max_depth=2)
        # Should find src/, tests/, requirements.txt, README.md
        assert len(results) > 0
        assert any("src" in r for r in results)
