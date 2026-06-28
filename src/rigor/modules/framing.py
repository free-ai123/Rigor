"""Problem framing helpers for pre-execution task clarification."""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

DIMENSION_QUESTIONS = {
    "what": "What exact deliverable should be produced?",
    "why": "What decision or outcome should this work support?",
    "who": "Who is the primary audience or user?",
    "how": "What format or interface should the output take?",
    "scope": "What is in scope, and what is explicitly out of scope?",
    "criteria": "What result would count as success?",
}

DIMENSION_LABELS = {
    "what": "What",
    "why": "Why",
    "who": "Who",
    "how": "How",
    "scope": "Scope",
    "criteria": "Success Criteria",
}

MODE_READY = "ready_to_execute"
MODE_ASSUMPTIONS = "proceed_with_assumptions"
MODE_CLARIFY = "needs_clarification"

LABEL_TO_KEY = {label: key for key, label in DIMENSION_LABELS.items()}


@dataclass
class ProblemFrame:
    original_request: str
    intent: str
    business_goal: str
    target_user: str
    deliverable: str
    scope: list[str]
    non_goals: list[str]
    constraints: list[str]
    success_criteria: list[str]
    assumptions: list[str]
    unknowns: list[str]
    clarification_questions: list[str]
    mode: str
    confidence: float
    confirmed_by_user: bool = False
    confirmation_status: str = "pending"
    confirmation_note: str = ""

    @property
    def should_block_execution(self) -> bool:
        return self.mode == MODE_CLARIFY

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["should_block_execution"] = self.should_block_execution
        return data


def _contains_any(text: str, patterns: list[str]) -> bool:
    return any(re.search(pattern, text, flags=re.IGNORECASE) for pattern in patterns)


def _infer_intent(request: str) -> str:
    lowered = request.lower()
    if _contains_any(lowered, [r"\bfix\b", r"\bbug\b", r"修复", r"报错", r"不能用"]):
        return "Fix or debug an existing issue."
    if _contains_any(lowered, [r"\banaly[sz]e\b", r"分析", r"调研", r"竞品"]):
        return "Analyze a topic and produce decision support."
    if _contains_any(lowered, [r"\boptimi[sz]e\b", r"优化", r"完善", r"改进"]):
        return "Improve an existing system or workflow."
    if _contains_any(lowered, [r"\bbuild\b", r"\bcreate\b", r"\bimplement\b", r"开发", r"做一个", r"生成"]):
        return "Build or create a new deliverable."
    if _contains_any(lowered, [r"\bwrite\b", r"\bdocument\b", r"写", r"文档", r"介绍"]):
        return "Write or revise content."
    return "Clarify and execute the requested work."


def _infer_deliverable(request: str) -> str:
    lowered = request.lower()
    if _contains_any(lowered, [r"\bapi\b", r"接口"]):
        return "API or backend service."
    if _contains_any(lowered, [r"\bapp\b", r"\bweb\b", r"网站", r"应用", r"系统", r"平台"]):
        return "Working software application."
    if _contains_any(lowered, [r"\breport\b", r"报告", r"分析", r"调研"]):
        return "Structured analysis report."
    if _contains_any(lowered, [r"\bprd\b", r"方案", r"计划", r"规划"]):
        return "Plan or product proposal."
    if _contains_any(lowered, [r"\breadme\b", r"文档", r"介绍", r"文章"]):
        return "Written document."
    return "Deliverable is not explicit."


def _dimension_presence(request: str) -> dict[str, bool]:
    text = request.lower()
    return {
        "what": _contains_any(
            text,
            [
                r"\bbuild\b",
                r"\bcreate\b",
                r"\bwrite\b",
                r"\btranslate\b",
                r"\banaly[sz]e\b",
                r"\bfix\b",
                r"开发",
                r"做",
                r"写",
                r"翻译",
                r"分析",
                r"修复",
                r"优化",
            ],
        ),
        "why": _contains_any(
            text, [r"\bso that\b", r"\bfor\b", r"\bin order\b", r"为了", r"以便", r"用于", r"用来", r"目标", r"为.+"]
        ),
        "who": _contains_any(
            text, [r"\baudience\b", r"\buser\b", r"\bcustomer\b", r"用户", r"客户", r"给", r"面向", r"团队"]
        ),
        "how": _contains_any(
            text,
            [
                r"\breport\b",
                r"\btable\b",
                r"\bppt\b",
                r"\bapi\b",
                r"\bcli\b",
                r"\bapp\b",
                r"\bemail\b",
                r"报告",
                r"表格",
                r"文档",
                r"页面",
                r"接口",
                r"命令",
                r"方案",
                r"邮件",
                r"英文",
                r"中文",
            ],
        ),
        "scope": _contains_any(
            text,
            [r"\bonly\b", r"\bexclude\b", r"\bscope\b", r"只", r"包括", r"包含", r"不做", r"不要", r"无需", r"范围"],
        ),
        "criteria": _contains_any(
            text,
            [
                r"\bsuccess\b",
                r"\bacceptance\b",
                r"\bmust\b",
                r"\bshould\b",
                r"成功",
                r"验收",
                r"通过",
                r"跑通",
                r"可用",
                r"必须",
                r"要能",
            ],
        ),
    }


def _extract_constraints(request: str) -> list[str]:
    constraints = []
    patterns = [
        (r"(今天|明天|本周|一天|一周|[0-9]+ ?天|[0-9]+ ?小时)", "Time constraint mentioned."),
        (r"(预算|成本|便宜|免费|cost|budget)", "Budget or cost constraint mentioned."),
        (r"(python|react|vue|node|fastapi|django|flask|typescript|java|go)", "Technology constraint mentioned."),
        (r"(不能|不要|必须|只允许|only|must|cannot)", "Hard requirement or restriction mentioned."),
    ]
    for pattern, label in patterns:
        if re.search(pattern, request, flags=re.IGNORECASE):
            constraints.append(label)
    return constraints


def _split_answer_items(answer: str) -> list[str]:
    items = []
    for raw in re.split(r"[\n,，;；]+", answer):
        item = raw.strip(" -\t")
        if item:
            items.append(item)
    return items


def _default_assumptions(missing: list[str], deliverable: str) -> list[str]:
    assumptions = []
    if "why" in missing:
        assumptions.append(
            "The work is intended to produce a practically usable result, not only a conceptual outline."
        )
    if "who" in missing:
        assumptions.append("The primary audience is the project owner and implementation team.")
    if "how" in missing and deliverable == "Deliverable is not explicit.":
        assumptions.append("A concise Markdown report is acceptable as the first output format.")
    if "scope" in missing:
        assumptions.append("Keep scope narrow and avoid unrelated features unless explicitly requested.")
    if "criteria" in missing:
        assumptions.append(
            "Success means the output is actionable, verifiable, and can drive the next engineering step."
        )
    return assumptions


def refine_problem_frame(frame: ProblemFrame, answers: dict[str, str]) -> ProblemFrame:
    """Apply human clarification answers to an existing problem frame."""
    normalized_answers = {key: value.strip() for key, value in answers.items() if value and value.strip()}
    if not normalized_answers:
        return frame

    answered_labels = {DIMENSION_LABELS[key] for key in normalized_answers if key in DIMENSION_LABELS}
    unknowns = [item for item in frame.unknowns if item not in answered_labels]

    intent = frame.intent
    business_goal = frame.business_goal
    target_user = frame.target_user
    deliverable = frame.deliverable
    scope = list(frame.scope)
    non_goals = list(frame.non_goals)
    constraints = list(frame.constraints)
    success_criteria = list(frame.success_criteria)

    if normalized_answers.get("what"):
        intent = normalized_answers["what"]
    if normalized_answers.get("why"):
        business_goal = normalized_answers["why"]
    if normalized_answers.get("who"):
        target_user = normalized_answers["who"]
    if normalized_answers.get("how"):
        deliverable = normalized_answers["how"]
    if normalized_answers.get("scope"):
        scope = _split_answer_items(normalized_answers["scope"])
    if normalized_answers.get("non_goals"):
        non_goals = _split_answer_items(normalized_answers["non_goals"])
    if normalized_answers.get("constraints"):
        constraints = _split_answer_items(normalized_answers["constraints"])
    if normalized_answers.get("criteria"):
        success_criteria = _split_answer_items(normalized_answers["criteria"])

    assumptions = [
        assumption
        for assumption in frame.assumptions
        if not (
            ("why" in normalized_answers and "practically usable" in assumption)
            or ("who" in normalized_answers and "primary audience" in assumption)
            or ("how" in normalized_answers and "Markdown report" in assumption)
            or ("scope" in normalized_answers and "Keep scope narrow" in assumption)
            or ("criteria" in normalized_answers and "Success means" in assumption)
        )
    ]

    clarification_questions = [DIMENSION_QUESTIONS[LABEL_TO_KEY[label]] for label in unknowns if label in LABEL_TO_KEY][
        :3
    ]
    if not unknowns:
        mode = MODE_READY
        confidence = max(frame.confidence, 0.9)
    elif len(unknowns) <= 2:
        mode = MODE_ASSUMPTIONS
        confidence = max(frame.confidence, 0.75)
    else:
        mode = MODE_CLARIFY
        confidence = frame.confidence

    return ProblemFrame(
        original_request=frame.original_request,
        intent=intent,
        business_goal=business_goal,
        target_user=target_user,
        deliverable=deliverable,
        scope=scope,
        non_goals=non_goals,
        constraints=constraints,
        success_criteria=success_criteria,
        assumptions=assumptions,
        unknowns=unknowns,
        clarification_questions=clarification_questions,
        mode=mode,
        confidence=round(confidence, 2),
        confirmed_by_user=False,
        confirmation_status="pending",
        confirmation_note="",
    )


def set_problem_frame_confirmation(frame: ProblemFrame, *, confirmed: bool, note: str | None = None) -> ProblemFrame:
    """Return a copy of a problem frame with user confirmation state."""
    return ProblemFrame(
        original_request=frame.original_request,
        intent=frame.intent,
        business_goal=frame.business_goal,
        target_user=frame.target_user,
        deliverable=frame.deliverable,
        scope=list(frame.scope),
        non_goals=list(frame.non_goals),
        constraints=list(frame.constraints),
        success_criteria=list(frame.success_criteria),
        assumptions=list(frame.assumptions),
        unknowns=list(frame.unknowns),
        clarification_questions=list(frame.clarification_questions),
        mode=frame.mode,
        confidence=frame.confidence,
        confirmed_by_user=confirmed,
        confirmation_status="confirmed" if confirmed else "rejected",
        confirmation_note=(note or "").strip(),
    )


def frame_problem(request: str, context: str | None = None, force_mode: str | None = None) -> ProblemFrame:
    """Create a deterministic problem frame from a user request."""
    normalized = " ".join(request.split())
    if not normalized:
        raise ValueError("request must not be empty")

    presence = _dimension_presence(normalized)
    missing = [DIMENSION_LABELS[key] for key, present in presence.items() if not present]
    missing_keys = [key for key, present in presence.items() if not present]
    deliverable = _infer_deliverable(normalized)
    constraints = _extract_constraints(normalized)

    vague_request = len(normalized) < 24 or _contains_any(
        normalized,
        [r"方案$", r"规划$", r"分析一下$", r"优化一下$", r"做一个.+方案", r"agent 方案"],
    )
    missing_count = len(missing_keys)

    if force_mode:
        mode = force_mode
    elif missing_count >= 4 and vague_request:
        mode = MODE_CLARIFY
    elif missing_count >= 2:
        mode = MODE_ASSUMPTIONS
    else:
        mode = MODE_READY

    confidence = max(0.2, min(0.95, 0.9 - missing_count * 0.1))
    if mode == MODE_CLARIFY:
        confidence = min(confidence, 0.55)
    elif mode == MODE_ASSUMPTIONS:
        confidence = min(confidence, 0.75)

    questions = [DIMENSION_QUESTIONS[key] for key in missing_keys[:3]]
    assumptions = _default_assumptions(missing_keys, deliverable)
    if context:
        assumptions.append("Additional context was provided and should be considered authoritative.")

    return ProblemFrame(
        original_request=normalized,
        intent=_infer_intent(normalized),
        business_goal="Explicitly stated." if presence["why"] else "Not explicit.",
        target_user="Explicitly stated." if presence["who"] else "Not explicit.",
        deliverable=deliverable,
        scope=["Explicit scope hint found."] if presence["scope"] else [],
        non_goals=["Avoid unrelated expansion until confirmed."] if not presence["scope"] else [],
        constraints=constraints,
        success_criteria=["Explicit success hint found."] if presence["criteria"] else [],
        assumptions=assumptions,
        unknowns=missing,
        clarification_questions=questions,
        mode=mode,
        confidence=round(confidence, 2),
    )


def format_problem_frame(frame: ProblemFrame) -> str:
    """Render a problem frame as Markdown."""
    status = "BLOCKED" if frame.should_block_execution else "READY"
    lines = [
        f"# Rigor Problem Frame: {status}",
        "",
        f"- Mode: `{frame.mode}`",
        f"- Confidence: `{frame.confidence:.2f}`",
        f"- Confirmation: `{frame.confirmation_status}`",
        f"- Intent: {frame.intent}",
        f"- Deliverable: {frame.deliverable}",
        f"- Business Goal: {frame.business_goal}",
        f"- Target User: {frame.target_user}",
        "",
        "## Original Request",
        frame.original_request,
        "",
        "## Scope",
    ]
    lines.extend(f"- {item}" for item in (frame.scope or ["Not explicit."]))
    lines.extend(["", "## Non-Goals"])
    lines.extend(f"- {item}" for item in (frame.non_goals or ["Not explicit."]))
    lines.extend(["", "## Constraints"])
    lines.extend(f"- {item}" for item in (frame.constraints or ["Not explicit."]))
    lines.extend(["", "## Success Criteria"])
    lines.extend(f"- {item}" for item in (frame.success_criteria or ["Not explicit."]))
    lines.extend(["", "## Assumptions"])
    lines.extend(f"- {item}" for item in (frame.assumptions or ["None."]))
    lines.extend(["", "## Unknowns"])
    lines.extend(f"- {item}" for item in (frame.unknowns or ["None."]))
    lines.extend(["", "## Clarification Questions"])
    lines.extend(f"{idx}. {question}" for idx, question in enumerate(frame.clarification_questions, start=1))
    if not frame.clarification_questions:
        lines.append("None.")
    lines.extend(["", "## User Confirmation"])
    lines.append(f"- Confirmed By User: `{str(frame.confirmed_by_user).lower()}`")
    lines.append(f"- Status: `{frame.confirmation_status}`")
    if frame.confirmation_note:
        lines.append(f"- Note: {frame.confirmation_note}")
    return "\n".join(lines).rstrip() + "\n"


def save_problem_frame(frame: ProblemFrame, output_dir: str | Path) -> tuple[Path, Path]:
    """Save Markdown and JSON problem-frame artifacts."""
    output_path = Path(output_dir).expanduser().resolve()
    output_path.mkdir(parents=True, exist_ok=True)
    md_path = output_path / "problem-frame.md"
    json_path = output_path / "problem-frame.json"
    md_path.write_text(format_problem_frame(frame), encoding="utf-8")
    json_path.write_text(json.dumps(frame.to_dict(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return md_path, json_path
