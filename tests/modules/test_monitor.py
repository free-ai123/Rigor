"""Tests for monitor compatibility helpers."""

from rigor.modules.monitor import _is_configured_value, _read_simple_yaml_value


def test_read_simple_yaml_value_reads_nested_model(tmp_path):
    config = tmp_path / "config.yaml"
    config.write_text(
        """
model:
  default: alibaba/qwen3.6-plus
  provider: alibaba
kanban:
  auto_decompose: true
""",
        encoding="utf-8",
    )

    assert _read_simple_yaml_value(config, "model.default") == "alibaba/qwen3.6-plus"
    assert _read_simple_yaml_value(config, "kanban.auto_decompose") == "true"


def test_is_configured_value_rejects_not_set():
    assert _is_configured_value("alibaba/qwen3.6-plus") is True
    assert _is_configured_value("Not set") is False
