# 🤖 Rigor: 自主 12 角色 AI 工程团队

> **从故事到生产环境** — 一个全自主、自愈合的 AI 软件工程团队，基于 Hermes Agent 构建。

<div align="center">
  <a href="README.md">🇺🇸 English</a> | <a href="README.zh.md">🇨🇳 中文文档</a>
</div>

[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB)](https://www.python.org/)
[![Framework](https://img.shields.io/badge/Built%20on-Hermes%20Agent-2b6cb0)](https://hermes-agent.nousresearch.com/)

## 🚀 简介

**Rigor** 是一个 AI 原生工程框架，模拟了一个完整的 12 角色软件团队。它超越了简单的代码生成，实现了结构化工作流 (SDD + TDD)、持续集成循环和自主自愈能力。

### ✨ 核心特性

#### 🧠 12 位 AI 专家
一个涵盖 SDLC 全流程的专业团队：
- **管理层**: 产品总监 (PM), 技术负责人 (Tech Lead), 协调者 (Orchestrator)
- **工程层**: 后端工程师, 前端工程师, 数据科学家
- **质量层**: 测试工程师 (QA), 安全审计员, 代码审查员
- **运维层**: DevOps 工程师, 技术文档工程师, 数据工程师

#### 🔄 自愈合 CI/CD 循环
Rigor 不仅能写代码，还能自动修代码。
- **Auto-Fix 引擎**: 自动检测 CI 失败或运行时错误。
- **智能任务创建**: 自动生成修复任务，附带错误上下文并分配给对应专家。
- **Webhook 集成**: 实时监听 GitHub/GitLab 事件。

#### 💬 Orchestrator Chat 优先
使用 Hermes 原生 orchestrator profile 作为主控入口：
- **交互更稳定**: 直接进入标准 Hermes chat CLI，不再依赖自研终端控件。
- **中文输入更友好**: 避开 TUI 输入法兼容问题，使用终端本身的输入路径。
- **专家路由**: 让 orchestrator 分析、规划、创建 Kanban 任务并委派给专家角色。

#### 🛠️ 5 层自主环境配置
Agent 可以自动配置自己的运行环境：
1. **依赖安装**: 自动安装 `pip`, `npm`, `go mod`。
2. **系统工具**: 检查系统级二进制文件 (Docker, FFmpeg 等)。
3. **环境变量**: 从模板生成 `.env` 并填充安全密钥。
4. **数据库**: 自动运行迁移 (Django, Alembic, Prisma)。
5. **服务启动**: 识别框架并启动应用 (FastAPI, Flask, Next.js)。

#### 📦 多平台 Git 支持
无缝集成你的工作流：
- **GitHub** (API v3)
- **GitLab** (API v4)
- **自动检测**: Rigor 自动识别你的远程仓库类型。

#### 🔍 RAG 知识库
为团队构建长期记忆：
- **Obsidian 兼容**: 索引带有 YAML Frontmatter 的 Markdown 文件。
- **全文检索**: 使用 SQLite FTS5 实现零依赖、高速检索。
- **上下文注入**: Agent 在启动时自动加载相关的历史决策和模式。

#### 🛡️ SDD + TDD 混合工作流
- **Problem Framing 前置门禁**: Orchestrator 在创建实现任务前先澄清 What/Why/Who/Scope/Success Criteria。
- **故事驱动 (SDD)**: PM 编写带有 Given/When/Then 验收标准的用户故事。
- **测试驱动 (TDD)**: QA 在实现开始前将 AC 转化为 BDD 测试。
- **契约驱动 API 门禁**: `rigor contract check` 对比 OpenAPI、后端真实路由、前端真实调用，并可对运行中的后端做 HTTP smoke，确保开发出的应用核心功能真的跑通。

---

## 📦 安装

### 前置条件
- **Python 3.10+**
- **Hermes Agent**: 可提前安装；一键脚本也会调用内置 Hermes 团队配置流程。

### 快速开始

```bash
git clone https://github.com/free-ai123/Rigor.git
cd Rigor
bash scripts/bootstrap.sh
```

这个命令会自动创建 `.venv`、安装 Rigor 运行时/安全依赖，并执行 Hermes 12 角色团队配置。只想安装 CLI、不配置 Hermes 团队时：

```bash
bash scripts/bootstrap.sh --skip-hermes
```

需要贡献者工具和已弃用的自研 TUI 依赖时：

```bash
bash scripts/bootstrap.sh --dev
```

安装后运行：

```bash
source .venv/bin/activate
rigor chat

# 或者不激活虚拟环境：
./scripts/rigor.sh chat
```

如果你打开了新的终端，需要重新执行 `source .venv/bin/activate` 后才能直接用 `rigor` 命令；不想激活时就继续用 `./scripts/rigor.sh`。

`rigor chat` 默认会启动 Rigor 的 `orchestrator` Hermes profile，并在启动前自动把用户当前 Hermes 的登录、provider 和模型配置同步到这个 profile。旧的 `rigor tui` 只保留为兼容别名，现在也会转到同一个 chat 流程。

---

## 📖 使用指南

### 🚀 Orchestrator Chat
启动主交互入口：
```bash
./scripts/rigor.sh chat
```

单次提问：
```bash
./scripts/rigor.sh chat "分析当前项目，并给出下一批维护任务"
```

只有明确要使用隔离的 profile 专属配置时，才跳过同步：
```bash
./scripts/rigor.sh chat --no-sync-profile
```

### 🛠️ 环境配置
自主配置项目环境 (依赖 + 环境变量 + 数据库)：
```bash
rigor setup -d /path/to/project
```

### 🔄 CI/CD Webhook 监听
启动监听服务以启用 Auto-Fix 循环：
```bash
rigor webhook --port 9999
```
*将你的 GitHub/GitLab Webhook 指向 `http://your-server:9999`。*

### 🧠 知识管理
索引你的 Obsidian 库并搜索上下文：
```bash
# 索引 vault 中的所有 markdown 文件
rigor knowledge --vault ./my-knowledge-base

# 搜索特定模式
rigor knowledge "如何实现用户认证"
```

### 📝 项目脚手架
生成带有 SDD 模板的新项目结构：
```bash
rigor init my-new-api
# 默认创建到 ~/projects/my-new-api

rigor init my-new-api --dir ~/projects/custom-api
rigor init my-new-api --projects-dir ~/work
```

### 🧭 Problem Framing / 任务框定
在 PRD、架构和实现之前先澄清并确认任务：
```bash
rigor frame "为内部营销活动开发一个短链接服务" --dir ~/projects/my-new-api --confirm
```

会写入：
```text
artifacts/orchestrator/problem-frame.md
artifacts/orchestrator/problem-frame.json
```

### 🛡️ 安全与质量
扫描依赖漏洞：
```bash
rigor scan
```

验证 OpenAPI、后端路由、前端调用和运行中后端是否一致：
```bash
rigor contract check \
  --spec artifacts/backend-engineer/api-spec.json \
  --backend src/server \
  --frontend src \
  --base-url http://localhost:8000
```

### 🗺️ 代码地图
生成用于 Agent 上下文选择的轻量 Python 符号地图：
```bash
rigor code-map --dir .
```

### 📊 报告生成
生成每日或每周进度报告：
```bash
rigor report daily
rigor report weekly
```

---

## 🏗️ 架构

```
┌──────────────────────────────────────────────────────────────────┐
│                  Rigor CLI / Orchestrator Chat                   │
├───────────────────────┬──────────────────────┬───────────────────┤
│    🧠 Agent 核心      │    🔄 自动化         │    📦 集成       │
│ - Hermes Profiles     │ - Auto-Fix Loop      │ - GitHub/GitLab   │
│ - SOUL.md 配置        │ - 环境配置 (5 层)    │ - Webhook Server  │
│ - Kanban 执行器       │ - CI/CD Webhooks     │ - Docker          │
├───────────────────────┴──────────────────────┴───────────────────┤
│    💾 数据层                                                     │
│ - SQLite Kanban DB     - RAG 知识库 (FTS5)                       │
│ - Session 日志         - Artifact 注册表                         │
└──────────────────────────────────────────────────────────────────┘
```

## 🗺️ 路线图

- [x] **Phase 0**: 12 角色团队, SDD/TDD, Kanban
- [x] **Phase 1**: Python CLI, 多 Git 平台支持, Orchestrator Chat, CI/CD Webhooks
- [x] **Phase 2**: Auto-Fix 自愈循环, 自主环境配置, RAG 知识库
- [ ] **Phase 3**: VS Code Extension, 浏览器 Agent 集成 (E2E 测试)
- [ ] **Phase 4**: 企业级特性 (SSO, 审批流, 多项目隔离)

## 🤝 贡献

欢迎提交 PR！请阅读 [贡献指南](CONTRIBUTING.md)。

## 📄 许可证

本项目采用 MIT 许可证 — 详见 [LICENSE](LICENSE) 文件。
