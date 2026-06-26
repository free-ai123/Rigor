"""Shared pytest fixtures for Rigor tests."""

import shutil
import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def tmp_workspace():
    """Create a temporary workspace with sample files."""
    tmp = tempfile.mkdtemp(prefix="rigor_test_")
    ws = Path(tmp)

    # Create sample Python project
    (ws / "src").mkdir()
    (ws / "src" / "__init__.py").write_text("")
    (ws / "src" / "main.py").write_text(
        "import os\n"
        "import json\n"
        "\n"
        "def hello(name: str) -> str:\n"
        "    return f'Hello, {name}!'\n"
        "\n"
        "if __name__ == '__main__':\n"
        "    print(hello('World'))\n"
    )
    (ws / "src" / "utils.py").write_text("def add(a, b):\n    return a + b\n\ndef subtract(a, b):\n    return a - b\n")
    (ws / "requirements.txt").write_text("pytest>=7.0\n")
    (ws / "README.md").write_text("# Test Project\n\nThis is a test project.")

    # Create a nested directory
    (ws / "tests").mkdir()
    (ws / "tests" / "test_main.py").write_text(
        "from src.main import hello\n\ndef test_hello():\n    assert hello('Alice') == 'Hello, Alice!'\n"
    )

    yield ws

    # Cleanup
    shutil.rmtree(tmp, ignore_errors=True)
