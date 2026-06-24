# Contributing to Rigor

Thank you for your interest in contributing! Rigor is an open-source AI engineering team built on top of [Hermes Agent](https://github.com/NousResearch/hermes-agent).

## Quick Links

- [Add a New Role](#add-a-new-role) — Create a new expert profile
- [Improve an Existing Role](#improve-an-existing-role) — Edit SOUL.md
- [Add Knowledge](#add-knowledge) — Contribute to the knowledge base
- [Report a Bug](#report-a-bug) — Issues and troubleshooting
- [Code of Conduct](#code-of-conduct)

## How Rigor Works

Rigor consists of:
- **12 Profile configurations** — Each role has a `SOUL.md` (system prompt) and `config.yaml` (model settings)
- **1 deployment script** — `scripts/setup-expert-team.sh` installs profiles and configures Kanban
- **1 structured knowledge base** — JSON files in `knowledge-base/structured/`
- **Documentation** — README, quickstart, and architecture guides

All changes are **SOUL.md + config + JSON** — no Python code required.

## Add a New Role

### 1. Create the Profile Directory

```
profiles/<role-name>/
├── SOUL.md
└── config.yaml
```

Use kebab-case for the role name (e.g., `ml-engineer`, `security-engineer`).

### 2. Write SOUL.md

Your SOUL.md must include these sections:

```markdown
# <Role Name> Profile

You are a <expertise> <role name>. You receive tasks via Kanban and execute them.

## Core Principles

- **Scope**: What this role does (be specific)
- **Boundary**: What this role does NOT do ("Never cross into...")
- **Bottom line**: Non-negotiable rules

## Workflow

### Startup Preparation: Read Upstream Artifacts
1. Read PRD (if applicable)
2. Read technical contracts (if applicable)
3. Check shared knowledge

### Execution (ReAct Mode)
**Follow Observe → Plan → Act → Verify cycle:**
1. **Observe**: Read kanban_show + artifacts + shared knowledge
2. **Plan**: Determine approach based on context
3. **Act**: Execute the task
4. **Verify**: Check output quality

### Artifact Registration
Write outputs to `$HERMES_KANBAN_WORKSPACE/artifacts/<role-name>/`:
- `output.md` — Description
- `config.json` — Description

### Structured Delivery
`kanban_complete` metadata must include:
```json
{
  "artifacts_created": ["artifacts/<role-name>/output.md"],
  "status_report": "artifacts/<role-name>/status-report.json"
}
```

## Structured Communication Protocol
JSON templates for cross-role communication.

## Prohibited Behaviors
- Must NOT do X
- Must NOT do Y

## Knowledge Capture
What to write to shared/ after task completion.

## Communication Style
How this role communicates.
```

### 3. Write config.yaml

```yaml
model:
  default: qwen3.7-max
providers: {}
fallback_providers: []
credential_pool_strategies: {}
toolsets:
- hermes-cli
agent:
  max_turns: 90
  gateway_timeout: 1800
  restart_drain_timeout: 180
  api_max_retries: 3
  service_tier: ''
  tool_use_enforcement: auto
```

### 4. Update the Orchestrator

Edit `profiles/orchestrator/SOUL.md`:
- Add the role to the "Available Expert Team" table
- Add the role to the "Project Type" activation table
- Update the workflow diagram if needed

### 5. Update setup-expert-team.sh

Add the role name to the `PROFILES` array:

```bash
PROFILES=(
    "orchestrator"
    ...
    "your-new-role"
)
```

### 6. Submit PR

- Title: `feat: add <role-name> profile`
- Include: What this role does, what it outputs, how it collaborates

## Improve an Existing Role

### Good Improvements
- Fix ambiguous instructions in SOUL.md
- Add missing communication protocols
- Improve artifact definitions
- Add more prohibited behaviors
- Fix typos or formatting

### Bad Improvements
- Remove sections
- Make boundaries less strict
- Change role to do things outside its scope

### How to Submit

1. Fork the repository
2. Edit `profiles/<role>/SOUL.md`
3. Test with `bash scripts/setup-expert-team.sh` (optional)
4. Submit PR with title: `improve(<role>): <description>`

## Add Knowledge

### Add a Decision

Create `knowledge-base/shared/decisions/NNN-title.md`:

```markdown
# NNN - Decision Title

## Status
Accepted (YYYY-MM-DD)

## Context
What problem led to this decision?

## Decision
What was decided?

## Consequences
- Positive: ...
- Negative: ...

## Implementation Guide
How to apply this decision.
```

### Add a Gotcha

Create `knowledge-base/shared/gotchas/<slug>.md`:

```markdown
# Gotcha Title

## Scenario
What happened?

## Root Cause
Why did it happen?

## Solution
How to fix it.

## Prevention
How to avoid it in future.
```

### Add a Pattern

Create `knowledge-base/shared/patterns/<slug>.md`:

```markdown
# Pattern Title

## When to Use
What situations call for this pattern?

## Solution
The pattern.

## Example
Concrete example.

## Caveats
What to watch out for.
```

### Update Knowledge Index

After adding a knowledge entry, update `knowledge-base/structured/knowledge-index.json`:

```json
{
  "id": "<type>-<slug>",
  "type": "decision|gotcha|pattern",
  "file": "decisions/<file>.md|gotchas/<file>.md|patterns/<file>.md",
  "title": "<title>",
  "tags": ["tag1", "tag2"],
  "status": "active",
  "created_at": "YYYY-MM-DD",
  "confidence": 0.9,
  "synonyms": ["synonym1", "synonym2"],
  "content_summary": "<3-5 sentence summary>",
  "relevance": {
    "project_types": ["web_app", "backend_api"],
    "roles": ["backend-engineer"],
    "phase": "implementation"
  },
  "summary": "<one-line summary>"
}
```

## Report a Bug

### What to Include

1. **Hermes version**: `hermes --version`
2. **What you expected**: What should have happened
3. **What actually happened**: Error messages, unexpected behavior
4. **Steps to reproduce**: Exact commands
5. **Profile affected**: Which role's SOUL.md is involved

### Example

```markdown
## Bug: QA Engineer not reading PRD

**Hermes version**: v0.5.0
**Profile**: qa-engineer

**Expected**: QA reads PRD before writing tests
**Actual**: QA skips PRD reading, writes generic tests

**Steps to reproduce**:
1. Create triage task
2. Wait for auto-decompose
3. Check QA task output

**SOUL.md section**: Line 15-17 (startup preparation)
```

## Code of Conduct

- Be respectful and constructive
- Focus on the issue, not the person
- English is the project language (issues, PRs, discussions)
- Chinese/Japanese README translations are provided for accessibility

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
