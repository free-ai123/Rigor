import json

from rigor.modules.framing import (
    MODE_ASSUMPTIONS,
    MODE_CLARIFY,
    format_problem_frame,
    frame_problem,
    save_problem_frame,
    set_problem_frame_confirmation,
)


def test_frame_problem_blocks_highly_vague_agent_plan():
    frame = frame_problem("帮我做一个 AI Agent 方案")

    assert frame.mode == MODE_CLARIFY
    assert frame.should_block_execution is True
    assert frame.clarification_questions
    assert "Who" in frame.unknowns


def test_frame_problem_can_proceed_with_assumptions_when_partially_clear():
    frame = frame_problem("帮我优化当前项目，让生成新项目默认到 ~/projects，成功标准是不污染 Rigor 仓库")

    assert frame.mode == MODE_ASSUMPTIONS
    assert frame.should_block_execution is False
    assert frame.assumptions
    assert "Success Criteria" not in frame.unknowns


def test_format_problem_frame_renders_status_and_questions():
    frame = frame_problem("帮我做一个方案")
    rendered = format_problem_frame(frame)

    assert "# Rigor Problem Frame: BLOCKED" in rendered
    assert "Clarification Questions" in rendered


def test_save_problem_frame_writes_markdown_and_json(tmp_path):
    frame = frame_problem("为产品团队写一份正式报告，分析中国市场，包含价格、功能和成功建议")

    md_path, json_path = save_problem_frame(frame, tmp_path)

    assert md_path.exists()
    data = json.loads(json_path.read_text(encoding="utf-8"))
    assert data["original_request"].startswith("为产品团队")
    assert data["should_block_execution"] is False
    assert data["confirmed_by_user"] is False
    assert data["confirmation_status"] == "pending"


def test_set_problem_frame_confirmation_marks_user_approval():
    frame = frame_problem("为产品团队写一份正式报告，分析中国市场，包含价格、功能和成功建议")

    confirmed = set_problem_frame_confirmation(frame, confirmed=True)

    assert confirmed.confirmed_by_user is True
    assert confirmed.confirmation_status == "confirmed"
    assert "Confirmation: `confirmed`" in format_problem_frame(confirmed)
