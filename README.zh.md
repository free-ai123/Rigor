# 🤖 Rigor: 自主 12 角色 AI 工程团队

> **从故事到生产环境** — 一个全自主、自愈合的 AI 软件工程团队，基于 Hermes Agent 构建。

<div align="center">
  <a href="README.md">🇺🇸 English</a> | <a href="README.zh.md">🇨🇳 中文文档</a>
</div>

[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.6%2B-3776AB)](https://www.python.org/)
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

#### 🖥️ 实时 TUI 仪表盘
在类似 `k9s` 的终端界面监控你的 AI 团队：
- **实时看板**: 观看任务从 TODO → DONE 的流转。
- **Agent 状态矩阵**: 查看谁在工作、谁空闲、谁被阻塞。
- **成本与 Token 追踪**: 实时监控 AI 资源消耗。

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
- **Gitea** / Gitee
- **自动检测**: Rigor 自动识别你的远程仓库类型。

#### 🔍 RAG 知识库
为团队构建长期记忆：
- **Obsidian 兼容**: 索引带有 YAML Frontmatter 的 Markdown 文件。
- **全文检索**: 使用 SQLite FTS5 实现零依赖、高速检索。
- **上下文注入**: Agent 在启动时自动加载相关的历史决策和模式。

#### 🛡️ SDD + TDD 混合工作流
- **故事驱动 (SDD)**: PM 编写带有 Given/When/Then 验收标准的用户故事。
- **测试驱动 (TDD)**: QA 在实现开始前将 AC 转化为 BDD 测试。

---

## 📦 安装

### 前置条件
- **Python 3.6+**
- **Hermes Agent**: Rigor 构建在 Hermes Agent 之上，用于 Profile 管理和 Kanban 执行。[安装 Hermes](https://hermes-agent.nousresearch.com/docs/)

### 快速开始

```bash
# 1. 克隆仓库
git clone https://github.com/free-ai123/Rigor.git
cd Rigor

# 2. 安装依赖
pip install -e ".[dev]"

# 3. 启动 TUI 仪表盘
rigor tui
```

---

## 📖 使用指南

### 🚀 交互式仪表盘
启动实时监控界面：
```bash
rigor tui
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
```

### 🛡️ 安全与质量
扫描依赖漏洞：
```bash
rigor scan
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
│                        Rigor CLI / TUI                           │
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
- [x] **Phase 1**: Python CLI, 多 Git 平台支持, TUI 仪表盘, CI/CD Webhooks
- [x] **Phase 2**: Auto-Fix 自愈循环, 自主环境配置, RAG 知识库
- [ ] **Phase 3**: VS Code Extension, 浏览器 Agent 集成 (E2E 测试)
- [ ] **Phase 4**: 企业级特性 (SSO, 审批流, 多项目隔离)

## 🤝 贡献

欢迎提交 PR！请阅读 [贡献指南](CONTRIBUTING.md)。

## 📄 许可证

本项目采用 MIT 许可证 — 详见 [LICENSE](LICENSE) 文件。
