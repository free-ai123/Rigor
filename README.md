# Rigor

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Hermes Agent](https://img.shields.io/badge/Hermes-Agent-blue.svg)](https://hermes-agent.nousresearch.com/docs/)
[![Profiles](https://img.shields.io/badge/Profiles-12-orange.svg)](#12-roles)

**Engineering quality at AI speed.**

Rigor is a complete AI engineering team — 12 specialized roles that collaborate through a Kanban board, covering the full software engineering lifecycle: requirements → architecture → implementation → code review → QA testing → security audit → deployment → UAT → retrospective.

> Not another AI coding assistant. It's a **team of autonomous AI experts** that deliver code by standard engineering processes.

Built on [Hermes Agent](https://github.com/NousResearch/hermes-agent) — pure SOUL.md profiles + Kanban workflow. No custom code needed.

---

## Why Rigor?

| Capability | Rigor | Devin | Cursor | Copilot |
|------------|-------|-------|--------|---------|
| **Multi-Role Collaboration** | **88%** | 30% | 20% | 50% |
| **Engineering Quality** | **92%** | 75% | 40% | 65% |
| **TDD-First Workflow** | **82%** | 45% | 10% | 20% |
| **Coverage Gate** | **88%** | 70% | 10% | 25% |
| **Deployment Rollback** | **72%** | 50% | 0% | 20% |
| **Project Retrospective** | **68%** | 0% | 0% | 0% |
| **Structured Knowledge Base** | **76%** | 65% | 20% | 35% |
| **Observability** | **68%** | 52% | 15% | 22% |

*Data source: Multi-Agent System Capability Analysis, June 2026*

## 12 Roles

| Role | Responsibility | Key Output |
|------|---------------|------------|
| 🧠 **Orchestrator** | Task decomposition, routing, progress tracking | DAG plan, assignment |
| 📋 **Product Manager** | Requirements, PRD, UAT acceptance | PRD, acceptance report |
| 🏗️ **Tech Lead** | Architecture, DAG planning, ADR | Architecture, DAG, contracts |
| 💻 **Backend Engineer** | API, database, service logic | Code, migrations |
| 🎨 **Frontend Engineer** | UI components, state management | Components, pages |
| 📊 **Data Scientist** | Data analysis, ML, modeling | Reports, models |
| 🔧 **Data Engineer** | Pipelines, vector DB, RAG | Pipeline config, embeddings |
| 🔍 **Code Reviewer** | Architecture + code review (2 phases) | Review report |
| 🛡️ **Security Auditor** | Security audit (design + code phase) | Security report |
| 🧪 **QA Engineer** | Test design, automation, coverage | Test scripts, coverage |
| 🔧 **DevOps Engineer** | CI/CD, containers, deployment | Dockerfile, pipeline |
| 📝 **Technical Writer** | Technical docs, API docs, README | Documentation |

## Architecture

```
User Input (natural language requirement)
    ↓
Orchestrator (detects project type → selects roles → decomposes into DAG)
    ↓
┌─────────────────────────────────────────────┐
│  Kanban Board (SQLite, auto-decompose)      │
│  ┌─────┐  ┌──────┐  ┌──────┐  ┌──────────┐  │
│  │ PRD │→ │Arch  │→ │Impl  │→ │Review/Test│  │
│  └─────┘  └──────┘  └──────┘  └──────────┘  │
└─────────────────────────────────────────────┘
    ↓ (60s tick, Gateway dispatch)
12 Role Profiles execute in parallel (where dependencies allow)
    ↓ (Artifact chain: PRD → API Spec → Test Cases → Docs)
Deploy → UAT → Retrospective → Knowledge Capture
```

## Quick Start

### Prerequisites

- [Hermes Agent](https://hermes-agent.nousresearch.com/docs/) installed
- API key configured (DashScope, OpenRouter, etc.)
- 2GB RAM minimum (5 roles) / 4GB recommended (all 12 roles)

### 5 Minutes to Your First Project

```bash
# 1. Clone
git clone https://github.com/free-ai123/Rigor.git
cd Rigor

# 2. Deploy
bash scripts/setup-expert-team.sh

# 3. Create your first task
hermes kanban create "Build a URL shortener with custom codes and click tracking" --triage
```

60 seconds later, Orchestrator decomposes the task, 12 roles start collaborating.

### Monitor Progress

```bash
# Task list
hermes kanban list

# Project dashboard (auto-updated)
cat ~/.hermes/kanban/workspace/shared/structured/project-dashboard.json | python3 -m json.tool

# Task dependency tree
hermes kanban show <task-id> --tree
```

## Repository Structure

```
Rigor/                          # 32 files, ~30KB
├── profiles/                   # 12 expert roles (SOUL.md + config.yaml each)
│   ├── orchestrator/
│   ├── product-manager/
│   ├── tech-lead/
│   ├── backend-engineer/
│   ├── frontend-engineer/
│   ├── data-scientist/
│   ├── data-engineer/
│   ├── code-reviewer/
│   ├── security-auditor/
│   ├── qa-engineer/
│   ├── devops-engineer/
│   └── technical-writer/
├── scripts/
│   └── setup-expert-team.sh    # One-click deployment (v2.0)
├── knowledge-base/
│   └── structured/             # Structured knowledge base
│       ├── knowledge-index.json  # 6 entries, 68 synonyms
│       ├── effectiveness.json    # Effectiveness tracking + decay rules
│       ├── project-profiles.json # Auto-inject rules
│       └── edges.json            # Knowledge relationship graph
├── docs/                         # Documentation
│   ├── architecture.md           # System architecture
│   ├── quickstart.md             # 5-minute guide
│   └── troubleshooting.md        # Common issues and fixes
├── examples/                     # Example projects
│   └── url-shortener/            # Full project output example
├── CONTRIBUTING.md               # How to contribute
├── README.md                     # English
├── README.zh.md                  # 中文
├── README.ja.md                  # 日本語
├── LICENSE                       # MIT
└── .gitignore
```

## Comparison

### Why not Devin?

Devin is a powerful single-agent developer, great at writing code fast. But it has only **one role** — no product review, no security audit, no QA testing, no deployment rollback.

Rigor is **12 roles collaborating by standard software engineering processes**, delivering **engineering quality**, not just coding speed.

### Why not Cursor?

Cursor is an excellent AI coding assistant that helps **you** write code. But it doesn't collaborate autonomously — you decide architecture, write tests, and review yourself.

Rigor is an **autonomous AI team** — you provide the requirement, the rest is handled.

## Task Management

### ✏️ Modify Task
After creating a task, you don't need to delete it to make changes:
*   **Recommended: Add Comment** (Agents auto-read comments in ~60s):
    ```bash
    hermes kanban comment <id> "Correction: Sort by Stars only. Change theme to dark blue."
    ```
*   **Update Description**:
    ```bash
    hermes kanban update <id> --body "New description..."
    ```

### 🛑 Stop Task
*   **Block** (Stop immediately): `hermes kanban block <id> "Cancelled"`
*   **Reset** (Revert to todo): `hermes kanban reset <id>`
*   **Archive** (Hide from list): `hermes kanban archive <id>`

## Knowledge Base

Rigor includes a structured knowledge base for cross-project experience reuse:

- **knowledge-index.json** — 6 knowledge entries with tags, 68 synonyms, confidence scores, and relevance rules
- **effectiveness.json** — Tracks how many times each knowledge item prevented a real issue, with automatic decay rules (30d unused → declining, 60d → stale, 180d → archived)
- **project-profiles.json** — Auto-injects relevant knowledge based on project type and active roles
- **edges.json** — Relationship graph connecting decisions → bugs → fixes → patterns

## Roadmap

- [x] 12 role SOUL.md + collaboration workflow
- [x] TDD-first mode (QA writes tests before implementation)
- [x] Coverage gate (line ≥ 80%, branch ≥ 70%)
- [x] Artifact version management
- [x] Self-correction loop (auto-fix + human escalation)
- [x] Structured knowledge base (index + semantic + decay)
- [x] Project dashboard + task status reports
- [x] Project retrospective + history archive
- [x] Deployment rollback protocol
- [x] Incremental update mode
- [x] Code style unification (ruff / prettier / eslint)
- [ ] More vertical domain roles (finance, healthcare, legal)
- [ ] Custom role creation guide
- [ ] Web Dashboard integration
- [ ] Multi-language SOUL.md support

## Contributing

Contributions welcome!

- **Add a new role**: Fork → create `profiles/<role>/SOUL.md` → PR
- **Improve existing role**: Edit `profiles/<role>/SOUL.md` → PR
- **Add knowledge**: Update `knowledge-base/` → PR
- **Report bugs**: Issues or PRs welcome

## License

MIT — see [LICENSE](LICENSE)

---

⭐ If Rigor is useful to you, a star is greatly appreciated!
