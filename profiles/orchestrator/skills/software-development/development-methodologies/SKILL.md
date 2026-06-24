---
name: development-methodologies
description: "Development process skills: planning (writing-plans), subagent execution, TDD, code review, systematic debugging, and spike experimentation."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [planning, subagent, tdd, code-review, debugging, spike, development-process]
    category: software-development
---

# Development Methodologies Suite

Six development process skills covering the full lifecycle: plan → experiment → implement → verify → review → debug.

---

## Mode A: Writing Implementation Plans

**Trigger:** Multi-step feature, complex requirements, delegating to subagents, user says "plan" or "/plan"

**Core principle:** A good plan makes implementation obvious. Bite-sized tasks (2-5 min each), exact file paths, complete code examples, exact commands with expected output.

### Plan Structure
```markdown
# [Feature] Implementation Plan
> For Hermes: Use subagent-driven-development skill to implement.
**Goal:** [One sentence]
**Architecture:** [2-3 sentences]
**Tech Stack:** [Key technologies]
---
### Task N: [Descriptive Name]
**Objective:** [One sentence]
**Files:** Create/Modify/Test with exact paths
**Steps:** Write test → Run (expect FAIL) → Implement → Run (expect PASS) → Commit
```

### Principles
- **DRY**: Extract shared logic, don't copy-paste
- **YAGNI**: Implement only what's needed now
- **TDD**: Every code task includes full TDD cycle
- **Frequent commits**: After every task

### Plan Mode
When invoked via `/plan`: write plan to `.hermes/plans/YYYY-MM-DD_HHMMSS-<slug>.md`, do NOT implement code.

---

## Mode B: Subagent-Driven Development

**Trigger:** Have an implementation plan, tasks are mostly independent, quality matters

**Core principle:** Fresh subagent per task + two-stage review (spec compliance → code quality) = high quality, fast iteration.

### Per-Task Workflow
1. Dispatch implementer subagent via `delegate_task(goal=..., context=..., toolsets=...)`
2. Dispatch spec compliance reviewer (check against original plan requirements)
3. Dispatch code quality reviewer (conventions, error handling, test coverage, security)
4. Mark task complete only when BOTH reviews pass

### Red Flags — Never Do
- Start implementation without a plan
- Skip reviews (spec OR quality)
- Dispatch multiple implementers for tasks touching same files
- Make subagent read the plan file (provide full text in context)
- Start code quality review before spec compliance passes
- Accept "close enough" on spec compliance

### Task Granularity
- **Too big:** "Implement user authentication system"
- **Right size:** "Create User model with email and password fields"

---

## Mode C: Test-Driven Development (TDD)

**Trigger:** New features, bug fixes, refactoring, behavior changes

**Iron law:** NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST.

### Red-Green-Refactor Cycle
1. **RED**: Write one minimal failing test (one behavior, clear name, real code not mocks)
2. **Verify RED**: Run test, confirm it fails for expected reason (feature missing, not typo)
3. **GREEN**: Write simplest code to pass. Hardcode, copy-paste, skip edge cases — we fix in refactor.
4. **Verify GREEN**: Run test, run ALL tests for regressions
5. **REFACTOR**: Remove duplication, improve names, extract helpers. Keep tests green.

### Common Rationalizations (all wrong)
| Excuse | Reality |
|--------|---------|
| "Too simple to test" | Simple code breaks. Test takes 30 seconds. |
| "I'll test after" | Tests passing immediately prove nothing. |
| "Already manually tested" | Ad-hoc ≠ systematic. No record, can't re-run. |
| "Deleting X hours is wasteful" | Sunk cost fallacy. Keeping unverified code is debt. |
| "TDD is dogmatic" | TDD IS pragmatic: finds bugs before commit, prevents regressions. |

### Verification Checklist
- [ ] Every new function has a test
- [ ] Watched each test fail before implementing
- [ ] Wrote minimal code to pass
- [ ] All tests pass, output pristine
- [ ] Edge cases and errors covered

---

## Mode D: Pre-Commit Code Review

**Trigger:** After implementing feature/bug fix, before `git commit` or `git push`

**Core principle:** No agent should verify its own work. Fresh context finds what you miss.

### Pipeline
1. Get diff: `git diff --cached` (split by file if >15K chars)
2. Static security scan: grep added lines for hardcoded secrets, shell injection, eval/exec, unsafe deserialization, SQL injection
3. Baseline tests + linting: Detect framework, run tests, capture baseline failures, count NEW failures
4. Self-review checklist: secrets, input validation, parameterized SQL, path validation, error handling, no debug prints
5. Independent reviewer subagent: `delegate_task` with ONLY diff + scan results (no shared context). Fail-closed: unparseable = fail.
6. Evaluate: All passed → commit. Any failures → auto-fix loop (max 2 cycles).
7. Auto-fix: Spawn THIRD agent context to fix ONLY reported issues. Re-verify.
8. Commit: `git add -A && git commit -m "[verified] <description>"`

---

## Mode E: Systematic Debugging

**Trigger:** ANY technical issue — test failures, bugs, unexpected behavior, performance problems

**Iron law:** NO FIXES WITHOUT ROOT CAUSE INVESTIGATION FIRST.

### Four Phases (MUST complete each before proceeding)
1. **Root Cause Investigation**: Read errors carefully → Reproduce consistently → Check recent changes → Gather evidence (logs, state, data flow) → Trace data flow upstream → Form hypothesis
2. **Pattern Analysis**: Find working examples → Compare against references → Identify differences → Understand dependencies
3. **Hypothesis & Testing**: Form single hypothesis ("X is root cause because Y") → Test minimally (one variable) → Verify → If wrong, new hypothesis
4. **Implementation**: Create failing test case → Implement single fix → Verify → If fix doesn't work: Rule of Three (3+ failures = question architecture)

### Red Flags — STOP and Return to Phase 1
- "Quick fix for now, investigate later"
- "Just try changing X and see"
- "I don't fully understand but this might work"
- "One more fix attempt" (when already tried 2+)
- Each fix reveals new problem in different place → question architecture

### Hermes Integration
- Python: `breakpoint()`, `debugpy`, `remote-pdb`, `pytest --pdb`
- Node: `node inspect`, `--inspect-brk`, `kill -SIGUSR1 <pid>`
- Multi-component: Add diagnostic instrumentation at each component boundary BEFORE proposing fixes

---

## Mode F: Spike (Throwaway Experimentation)

**Trigger:** "let me try this", "is this even possible?", "compare A vs B", "quick prototype"

### Core Method
```
decompose → research → build → verdict → iterate
```

### Spike Types
- **Standard**: One approach answering one question
- **Comparison**: Same question, different approaches (002a/002b)

### Workflow
1. **Decompose**: 2-5 independent feasibility questions as Given/When/Then table, ordered by risk
2. **Research**: Brief competing approaches, pick one, state why
3. **Build**: One directory per spike (`spikes/NNN-name/`). Bias toward something user can interact with (CLI, HTML page, web server, test).
4. **Verdict**: VALIDATED / PARTIAL / INVALIDATED in README.md with evidence

### Output
```
spikes/
├── 001-websocket-streaming/
│   ├── README.md  (includes Verdict section)
│   └── main.py
└── 002a-pdf-parse-pdfjs/
    ├── README.md
    └── parse.py
```

### Key Rules
- Depth over speed — test edge cases, follow surprising findings
- Hardcode everything — it's a spike, not production
- INVALIDATED is a successful spike (you learned something)
- Comparison spikes: build back-to-back, then head-to-head table