# 🤖 Rigor: The Autonomous 12-Role AI Engineering Team

> **From Story to Production** — A fully autonomous, self-healing AI software engineering team powered by Hermes Agent.

<div align="center">
  <a href="README.md">🇺🇸 English</a> | <a href="README.zh.md">🇨🇳 中文文档</a>
</div>

[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB)](https://www.python.org/)
[![Framework](https://img.shields.io/badge/Built%20on-Hermes%20Agent-2b6cb0)](https://hermes-agent.nousresearch.com/)

## 🚀 Overview

**Rigor** is an AI-native engineering framework that simulates a complete 12-role software team. It goes beyond simple code generation by implementing structured workflows (SDD + TDD), continuous integration loops, and autonomous self-healing capabilities.

### ✨ Key Features

#### 🧠 12 Expert AI Agents
A specialized team handling every stage of the SDLC:
- **Management**: Product Manager, Tech Lead, Orchestrator
- **Engineering**: Backend Engineer, Frontend Engineer, Data Scientist
- **Quality**: QA Engineer, Security Auditor, Code Reviewer
- **Operations**: DevOps Engineer, Technical Writer, Data Engineer

#### 🔄 Self-Healing CI/CD Loop
Rigor doesn't just write code; it fixes it.
- **Auto-Fix Engine**: Automatically detects CI failures or runtime errors.
- **Smart Task Creation**: Generates repair tasks with error context and assigns them to the correct agent.
- **Webhook Integration**: Listens to GitHub/GitLab events in real-time.

#### 💬 Orchestrator Chat First
Use Hermes' native orchestrator profile as the primary control surface:
- **Stable interaction**: Talk directly to the orchestrator in the standard Hermes chat CLI.
- **Chinese input friendly**: Avoid custom terminal widgets and rely on the shell/terminal input path.
- **Expert routing**: Ask the orchestrator to analyze, plan, create Kanban tasks, and delegate to specialist roles.

#### 🛠️ 5-Layer Autonomous Environment Setup
Agents can configure their own execution environment:
1. **Dependencies**: Auto-install `pip`, `npm`, or `go mod`.
2. **System Tools**: Verify binaries (Docker, FFmpeg, etc.).
3. **Env Vars**: Generate `.env` from templates with secure secrets.
4. **Database**: Run migrations (Django, Alembic, Prisma) automatically.
5. **Service**: Detect and start the application (FastAPI, Flask, Next.js).

#### 📦 Multi-Platform Git Support
Seamless integration with your workflow:
- **GitHub** (API v3)
- **GitLab** (API v4)
- **Auto-Detection**: Rigor automatically detects your remote origin.

#### 🔍 RAG Knowledge Base
Build a long-term memory for your team:
- **Obsidian Compatible**: Indexes Markdown files with YAML frontmatter.
- **Semantic Search**: Uses SQLite FTS5 for zero-dependency, high-speed retrieval.
- **Context Injection**: Agents automatically load relevant past decisions and patterns.

#### 🛡️ SDD + TDD Hybrid Workflow
- **Problem Framing Gate**: The orchestrator clarifies What/Why/Who/Scope/Success Criteria before creating implementation work.
- **Story-Driven (SDD)**: PM writes User Stories with Given/When/Then Acceptance Criteria.
- **Test-Driven (TDD)**: QA converts AC into BDD tests before implementation begins.
- **Contract-Driven API Gate**: `rigor contract check` compares OpenAPI, backend routes, frontend calls, and optional live HTTP smoke so the built app can actually run through core functions.

---

## 📦 Installation

### Prerequisites
- **Python 3.10+**
- **Hermes Agent**: optional before bootstrap. The bootstrap script can launch the bundled Hermes team setup for you.

### Quick Start

```bash
git clone https://github.com/free-ai123/Rigor.git
cd Rigor
bash scripts/bootstrap.sh
```

The bootstrap command creates `.venv`, installs Rigor with runtime and security tooling, and runs the Hermes expert-team setup. For CLI-only installation:

```bash
bash scripts/bootstrap.sh --skip-hermes
```

For contributor tooling and the deprecated custom TUI dependencies:

```bash
bash scripts/bootstrap.sh --dev
```

Run the CLI after bootstrap:

```bash
source .venv/bin/activate
rigor chat

# Or without activating the virtualenv:
./scripts/rigor.sh chat
```

If you open a new terminal, activate `.venv` again before using the plain `rigor` command, or keep using `./scripts/rigor.sh`.

`rigor chat` launches the Rigor `orchestrator` Hermes profile and automatically syncs the user's current Hermes login/provider/model into that profile first. The old `rigor tui` command is kept only as a deprecated compatibility alias and now forwards to the same chat flow.

---

## 📖 Usage

### 🚀 Orchestrator Chat
Launch the primary interactive interface:
```bash
./scripts/rigor.sh chat
```

Run a one-shot prompt:
```bash
./scripts/rigor.sh chat "Analyze this project and propose the next maintenance tasks"
```

Skip profile sync only when you explicitly want to use isolated profile-specific config:
```bash
./scripts/rigor.sh chat --no-sync-profile
```

### 🛠️ Environment Setup
Autonomously configure a project environment (Dependencies + Env Vars + DB):
```bash
rigor setup -d /path/to/project
```

### 🔄 CI/CD Webhook Listener
Start the listener to enable Auto-Fix loops:
```bash
rigor webhook --port 9999
```
*Point your GitHub/GitLab webhook to `http://your-server:9999`.*

### 🤖 Auto-Fix Background Worker
Start the self-healing daemon to automatically fix failed tasks:
```bash
rigor watch-fix --workspace /path/to/project
```
*Monitors the Kanban for `auto-fix` tasks, runs linters/tests, and updates status.*

### 🧠 Knowledge Management
Index your Obsidian vault and search for context:
```bash
# Index all markdown files in the vault
rigor knowledge --vault ./my-knowledge-base

# Search for specific patterns
rigor knowledge "how to implement auth"
```

### 📝 Project Scaffolding
Generate a new project structure with SDD templates:
```bash
rigor init my-new-api
# Creates ~/projects/my-new-api by default

rigor init my-new-api --dir ~/projects/custom-api
rigor init my-new-api --projects-dir ~/work
```

### 🧭 Problem Framing
Clarify and confirm the task before PRD, architecture, or implementation:
```bash
rigor frame "Build a URL shortener for internal marketing campaigns" --dir ~/projects/my-new-api --confirm
```

This writes:
```text
artifacts/orchestrator/problem-frame.md
artifacts/orchestrator/problem-frame.json
```

### 🛡️ Security & Quality
Scan for dependency vulnerabilities:
```bash
rigor scan
```

Verify API contracts across OpenAPI, backend routes, frontend calls, and a live backend:
```bash
rigor contract check \
  --spec artifacts/backend-engineer/api-spec.json \
  --backend src/server \
  --frontend src \
  --base-url http://localhost:8000
```

### 🗺️ Code Map
Generate a compact Python symbol map for agent context selection:
```bash
rigor code-map --dir .
```

### 📊 Reporting
Generate daily or weekly progress reports:
```bash
rigor report daily
rigor report weekly
```

---

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                  Rigor CLI / Orchestrator Chat                   │
├───────────────────────┬──────────────────────┬───────────────────┤
│    🧠 Agent Core      │    🔄 Automation     │    📦 Integrations │
│ - Hermes Profiles     │ - Auto-Fix Loop      │ - GitHub/GitLab   │
│ - SOUL.md Config      │ - Env Setup (5-Layer)│ - Webhook Server  │
│ - Kanban Executor     │ - CI/CD Webhooks     │ - Docker          │
├───────────────────────┴──────────────────────┴───────────────────┤
│    💾 Data Layer                                                 │
│ - SQLite Kanban DB     - RAG Knowledge Base (FTS5)               │
│ - Session Logs         - Artifact Registry                       │
└──────────────────────────────────────────────────────────────────┘
```

## 🗺️ Roadmap

- [x] **Phase 0**: 12-Role Team, SDD/TDD, Kanban
- [x] **Phase 1**: Python CLI, Multi-Git, Orchestrator Chat, CI/CD Webhooks
- [x] **Phase 2**: Auto-Fix Loop, Autonomous Env Setup, RAG Knowledge Base
- [ ] **Phase 3**: VS Code Extension, Browser Agent Integration (E2E)
- [ ] **Phase 4**: Enterprise Features (SSO, Approval Workflows, Multi-Project)

## 🤝 Contributing

We welcome contributions! Please read our [Contributing Guide](CONTRIBUTING.md).

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
