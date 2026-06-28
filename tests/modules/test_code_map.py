"""Tests for lightweight code map generation."""

from rigor.modules.code_map import build_code_map, format_code_map


def test_build_code_map_extracts_symbols(tmp_path):
    source = tmp_path / "app.py"
    source.write_text(
        "import os\n\nclass Service:\n    pass\n\ndef run():\n    return os.getcwd()\n",
        encoding="utf-8",
    )

    code_map = build_code_map(str(tmp_path))

    assert code_map["file_count"] == 1
    assert code_map["files"][0]["path"] == "app.py"
    assert {"name": "class Service", "line": 3} in code_map["files"][0]["symbols"]
    assert {"name": "def run", "line": 6} in code_map["files"][0]["symbols"]


def test_format_code_map_outputs_markdown(tmp_path):
    (tmp_path / "app.py").write_text("def run():\n    pass\n", encoding="utf-8")

    rendered = format_code_map(build_code_map(str(tmp_path)))

    assert "# Code Map" in rendered
    assert "`def run`" in rendered
