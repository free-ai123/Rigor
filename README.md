# 🤖 Rigor: The Autonomous 12-Role AI Engineering Team

> **From Story to Production** — A fully autonomous, self-healing AI software engineering team powered by Hermes Agent.

[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.6%2B-3776AB)](https://www.python.org/)
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

#### 🖥️ Real-time TUI Dashboard
Monitor your AI team in a `k9s`-style terminal interface:
- **Live Kanban**: Watch tasks move from TODO → DONE.
- **Agent Status Matrix**: See who is working, idle, or blocked.
- **Cost & Token Tracking**: Real-time monitoring of AI resource usage.

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
- **Gitea** / Gitee
- **Auto-Detection**: Rigor automatically detects your remote origin.

#### 🔍 RAG Knowledge Base
Build a long-term memory for your team:
- **Obsidian Compatible**: Indexes Markdown files with YAML frontmatter.
- **Semantic Search**: Uses SQLite FTS5 for zero-dependency, high-speed retrieval.
- **Context Injection**: Agents automatically load relevant past decisions and patterns.

#### 🛡️ SDD + TDD Hybrid Workflow
- **Story-Driven (SDD)**: PM writes User Stories with Given/When/Then Acceptance Criteria.
- **Test-Driven (TDD)**: QA converts AC into BDD tests before implementation begins.

---

## 📦 Installation

### Prerequisites
- **Python 3.6+**
- **Hermes Agent**: Rigor is built on top of Hermes Agent for profile management and Kanban execution. [Install Hermes](https://hermes-agent.nousresearch.com/docs/)

### Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/free-ai123/Rigor.git
cd Rigor

# 2. Install dependencies
pip install -e ".[dev]"

# 3. Launch the TUI Dashboard
rigor tui
```

---

## 📖 Usage

### 🚀 Interactive Dashboard
Launch the real-time monitoring interface:
```bash
rigor tui
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
```

### 🛡️ Security & Quality
Scan for dependency vulnerabilities:
```bash
rigor scan
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
│                        Rigor CLI / TUI                           │
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
- [x] **Phase 1**: Python CLI, Multi-Git, TUI Dashboard, CI/CD Webhooks
- [x] **Phase 2**: Auto-Fix Loop, Autonomous Env Setup, RAG Knowledge Base
- [ ] **Phase 3**: VS Code Extension, Browser Agent Integration (E2E)
- [ ] **Phase 4**: Enterprise Features (SSO, Approval Workflows, Multi-Project)

## 🤝 Contributing

We welcome contributions! Please read our [Contributing Guide](CONTRIBUTING.md).

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
