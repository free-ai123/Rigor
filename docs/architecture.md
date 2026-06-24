# Architecture

Rigor is a multi-agent engineering team that runs on top of [Hermes Agent](https://github.com/NousResearch/hermes-agent). This document explains how the system works.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    User Input                           │
│         (natural language requirement)                   │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│              Orchestrator Profile                       │
│  ┌───────────┐  ┌──────────┐  ┌──────────────────────┐  │
│  │ Detect    │→ │ Select   │→ │ Decompose into DAG   │  │
│  │ Type      │  │ Roles    │  │ (14+ tasks)          │  │
│  └───────────┘  └──────────┘  └──────────────────────┘  │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│              Kanban Board (SQLite)                       │
│                                                         │
│  ┌─────────┐  ┌──────────┐  ┌────────┐  ┌────────────┐  │
│  │ T0: PM  │→ │T0.5: TL  │→ │ T1-T6  │→ │ T7: Review │  │
│  │  PRD    │  │  Arch    │  │ Impl   │  │ T8: QA     │  │
│  └─────────┘  └──────────┘  └────────┘  │ T9: Sec    │  │
│                                          │ T10: DevOps│  │
│                                          └─────┬──────┘  │
│                                                ▼         │
│                                        ┌────────────┐    │
│                                        │ T11-T13    │    │
│                                        │ Deploy/UAT │    │
│                                        │ Retro/Docs │    │
│                                        └────────────┘    │
└────────────────────┬────────────────────────────────────┘
                     │  (60s tick, auto-decompose)
                     ▼
┌─────────────────────────────────────────────────────────┐
│              12 Role Profiles (Hermes Gateways)          │
│                                                         │
│  Each profile runs as an independent Hermes instance    │
│  with its own SOUL.md (system prompt), config.yaml,     │
│  skills, and memory. They share:                        │
│  - Kanban board (task queue)                            │
│  - Workspace directory (artifact exchange)              │
│  - Knowledge base (cross-project experience)            │
└─────────────────────────────────────────────────────────┘
```

## Core Components

### 1. SOUL.md (System Prompts)

Each role has a `SOUL.md` that defines:
- **Role definition**: What expertise this role has
- **Core principles**: Scope, boundaries, non-negotiables
- **Workflow**: Startup preparation → ReAct execution → Artifact registration → Structured delivery
- **Communication protocols**: JSON templates for cross-role communication
- **Prohibited behaviors**: What this role must NOT do
- **Knowledge capture**: What to write to shared/ after completion

**Key design principle**: SOUL.md is loaded fresh every message — no restart needed. Changes take effect immediately.

### 2. Kanban Board (SQLite)

The Kanban board (`~/.hermes/kanban.db`) is the hard boundary between roles:
- **Tasks**: Created by Orchestrator with status, assignee, parents (dependencies)
- **Auto-decompose**: 60-second tick — LLM reads profile roster, splits triage tasks into DAG
- **Dispatch**: Gateway finds ready tasks → matches assignee → spawns worker
- **Failure handling**: Auto-reclaims stale claims, blocks after 5 consecutive spawn failures

### 3. Artifact Exchange

Roles communicate through a shared workspace directory:

```
$HERMES_KANBAN_WORKSPACE/
├── artifacts/
│   ├── product-manager/
│   │   ├── prd.md                    # Requirements doc
│   │   └── user-stories.json         # Structured user stories
│   ├── tech-lead/
│   │   ├── dag-plan.json             # Task dependency graph
│   │   └── module-contracts.json     # Module interfaces
│   ├── backend-engineer/
│   │   ├── api-spec.json             # OpenAPI 3.0 spec
│   │   └── db-schema.sql             # Database migrations
│   ├── frontend-engineer/
│   │   ├── component-tree.md         # Component hierarchy
│   │   └── api-integration.md        # API integration guide
│   ├── qa-engineer/
│   │   ├── test-report.md            # Test results
│   │   └── test-suite/               # Automated tests
│   └── ... (other roles)
└── shared/
    ├── decisions/                    # Architecture Decision Records
    ├── patterns/                     # Reusable implementation patterns
    ├── gotchas/                      # Pitfalls and how to avoid them
    ├── retrospectives/               # Project retrospective reports
    ├── history/                      # Cross-project history archive
    └── structured/                   # Machine-readable knowledge
        ├── knowledge-index.json      # Global knowledge index
        ├── effectiveness.json        # Knowledge effectiveness tracking
        ├── project-profiles.json     # Auto-injection rules
        └── edges.json                # Knowledge relationship graph
```

### 4. Knowledge Base

The structured knowledge base enables cross-project experience reuse:

- **knowledge-index.json**: 6 entries with tags, 68 synonyms, confidence scores, relevance rules
- **effectiveness.json**: Tracks how many times each knowledge prevented a real issue, with automatic decay
- **project-profiles.json**: Auto-injects relevant knowledge based on project type and active roles
- **edges.json**: Relationship graph connecting decisions → bugs → fixes → patterns

### 5. Gateway Dispatcher

Each role runs as an independent Hermes Gateway process:
- **Isolation**: Separate sessions, tools, memory per profile
- **Coordination**: Shared Kanban board for task exchange
- **Resource management**: Each Gateway uses ~90-300MB RAM; full team needs ~3.5GB
- **Auto-start/stop**: Roles can be started/stopped independently to save resources

## Data Flow

### Task Creation Flow
```
1. User creates triage task
2. Gateway dispatcher picks it up (60s interval)
3. Orchestrator decomposes into DAG
4. Tasks created in kanban.db with parent/child links
5. Gateway dispatches to matching profiles
```

### Artifact Chain Flow
```
PM writes PRD → TechLead writes DAG + contracts
  → Backend writes API spec (reads PRD + contracts)
  → Frontend writes components (reads PRD + API spec)
  → QA writes tests (reads PRD + API spec)
  → Security audits (reads PRD + API spec + contracts)
  → DevOps deploys (reads API spec + contracts)
  → PM does UAT (reads PRD + all artifacts)
  → Writer writes docs (reads all artifacts)
  → Orchestrator writes retrospective (reads everything)
```

### Self-Correction Flow
```
Reviewer finds defect → Creates fix task (assignee=original author)
  → Fix task includes full context (file, line, error output)
  → Author fixes → Re-review by original reviewer
  → If fail again → Retry (max 3 times)
  → If fail 3 times → Escalation report to user
```

## Project Types and Role Activation

| Type | Roles Activated | Roles Skipped |
|------|----------------|---------------|
| 🌐 Web App | All 12 | None |
| 🔌 Backend API | 8 roles | frontend, data-scientist, data-engineer |
| 📊 Data/ML | 5 roles | backend, frontend, data-engineer, devops |
| 🤖 RAG/AI | 8 roles | frontend, data-scientist |
| 🛠️ Internal Tool | 5 roles | PM, TL, Sec, DS, DE |
| 🐛 Bug Fix | 3-4 roles | PM, TL, Sec, DS, DE, TW |
| 📝 Docs | 2 roles | All engineering roles |
| 🗄️ Infrastructure | 3 roles | All development roles |

## Quality Gates

| Gate | Condition | Action on Failure |
|------|-----------|------------------|
| Code Review | No critical findings | Block → Fix task → Re-review |
| Security Audit | 0 Critical/High vulnerabilities | Block → Fix task → Re-audit |
| QA Test | 100% pass, line ≥ 80%, branch ≥ 70% | Block → Fix task → Re-test |
| UAT | All PRD acceptance criteria met | Block → Fix task → Re-UAT |

## Observability

- **Project Dashboard**: `project-dashboard.json` — Progress %, quality score (0-100), risk level
- **Task Status Reports**: `status-report.json` per role — Duration, artifacts, code changes, confidence
- **Knowledge Effectiveness**: `effectiveness.json` — Read count, prevented count, trend, confidence decay
- **History Archive**: `history/<project>.json` — Cross-project metrics for trend analysis

## What Rigor Is NOT

- **Not a code generator**: It doesn't write code on its own — roles execute through Hermes tool calls
- **Not a framework**: It's configuration (SOUL.md + YAML + JSON), not Python code
- **Not a SaaS**: It runs on your machine via Hermes Agent
- **Not a replacement for humans**: Humans define requirements, review outputs, and intervene when auto-fix fails 3 times

## Extending Rigor

See [CONTRIBUTING.md](../CONTRIBUTING.md) for detailed instructions on:
- Adding a new role
- Improving an existing role
- Adding knowledge entries
- Reporting bugs
