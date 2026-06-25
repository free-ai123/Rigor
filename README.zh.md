# Rigor

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Hermes Agent](https://img.shields.io/badge/Hermes-Agent-blue.svg)](https://hermes-agent.nousresearch.com/docs/)
[![Profiles](https://img.shields.io/badge/Profiles-12-orange.svg)](#12-个角色)

**以 AI 的速度，交付工程级的质量。**

Rigor 是一个完整的 AI 工程团队 — 12 个专业角色通过 Kanban 协作，覆盖软件工程全生命周期：需求 → 架构 → 实现 → 代码审查 → QA 测试 → 安全审计 → 部署 → UAT → 复盘。

> 不是又一个 AI 编程助手。是一个**按标准工程流程交付代码的自主 AI 专家团队**。

基于 [Hermes Agent](https://github.com/NousResearch/hermes-agent) — 纯 SOUL.md 配置 + Kanban 工作流。无需编写任何自定义代码。

---

## 为什么选 Rigor？

| 能力 | Rigor | Devin | Cursor | Copilot |
|------|-------|-------|--------|---------|
| **多角色协作** | **88%** | 30% | 20% | 50% |
| **工程质量** | **92%** | 75% | 40% | 65% |
| **TDD 优先** | **82%** | 45% | 10% | 20% |
| **覆盖率门禁** | **88%** | 70% | 10% | 25% |
| **部署回滚** | **72%** | 50% | 0% | 20% |
| **项目复盘** | **68%** | 0% | 0% | 0% |
| **结构化知识库** | **76%** | 65% | 20% | 35% |
| **可观测性** | **68%** | 52% | 15% | 22% |

*数据来源：多 Agent 系统能力对比分析，2026 年 6 月*

## 12 个角色

| 角色 | 职责 | 关键输出 |
|------|------|---------|
| 🧠 **Orchestrator** | 任务分解、路由、进度跟踪 | DAG 任务图、分配方案 |
| 📋 **Product Manager** | 需求分析、PRD、UAT 验收 | PRD 文档、验收报告 |
| 🏗️ **Tech Lead** | 技术架构、任务拆解、ADR | 架构决策、DAG 图、模块契约 |
| 💻 **Backend Engineer** | API、数据库、服务逻辑 | 代码、迁移脚本 |
| 🎨 **Frontend Engineer** | UI 组件、状态管理 | 组件、页面 |
| 📊 **Data Scientist** | 数据分析、ML、建模 | 报告、模型 |
| 🔧 **Data Engineer** | 数据管道、向量库、RAG | Pipeline 配置、Embedding 集成 |
| 🔍 **Code Reviewer** | 架构审查 + 代码审查（两阶段） | 审查报告 |
| 🛡️ **Security Auditor** | 安全审计（设计期 + 代码期） | 安全报告 |
| 🧪 **QA Engineer** | 测试设计、自动化测试、覆盖率 | 测试脚本、覆盖率报告 |
| 🔧 **DevOps Engineer** | CI/CD、容器化、部署 | Dockerfile、Pipeline |
| 📝 **Technical Writer** | 技术文档、API 文档 | 文档 |

## 架构

```
用户输入需求（自然语言）
    ↓
Orchestrator（判断项目类型 → 选择角色子集 → 拆解为 DAG）
    ↓
┌─────────────────────────────────────────────┐
│  Kanban 看板（SQLite，自动分解）             │
│  ┌─────┐  ┌──────┐  ┌──────┐  ┌──────────┐  │
│  │ PRD │→ │架构  │→ │实现  │→ │审查/测试  │  │
│  └─────┘  └──────┘  └──────┘  └──────────┘  │
└─────────────────────────────────────────────┘
    ↓（60 秒周期，Gateway 调度）
12 个角色并行执行（依赖允许的地方）
    ↓（Artifact 传递链：PRD → API Spec → 测试用例 → 文档）
部署 → UAT → 复盘 → 知识沉淀
```

## 快速开始

### 前提条件

- 已安装 [Hermes Agent](https://hermes-agent.nousresearch.com/docs/)
- 已配置 API Key（DashScope、OpenRouter 等）
- 至少 2GB RAM（5 角色）/ 推荐 4GB（完整 12 角色）

### 5 分钟上手

```bash
# 1. 克隆
git clone https://github.com/free-ai123/Rigor.git
cd Rigor

# 2. 部署
bash scripts/setup-expert-team.sh

# 3. 创建第一个任务
hermes kanban create "做一个短链接服务，支持自定义后缀和点击统计" --triage
```

60 秒后，Orchestrator 自动拆解任务，12 个角色开始协作。

### 查看进度

```bash
# 任务列表
hermes kanban list

# 项目仪表盘（自动更新）
cat ~/.hermes/kanban/workspace/shared/structured/project-dashboard.json | python3 -m json.tool

# 任务依赖树
hermes kanban show <task-id> --tree
```

## 仓库结构

```
Rigor/                          # 32 个文件，约 30KB
├── profiles/                   # 12 个专家角色（每个含 SOUL.md + config.yaml）
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
│   └── setup-expert-team.sh    # 一键部署脚本（v2.0）
├── knowledge-base/
│   └── structured/             # 结构化知识库
│       ├── knowledge-index.json  # 6 条知识，68 个同义词
│       ├── effectiveness.json    # 效果追踪 + 衰减规则
│       ├── project-profiles.json # 自动注入规则
│       └── edges.json            # 知识关系图谱
├── docs/                         # 文档
│   ├── architecture.md           # 系统架构
│   ├── quickstart.md             # 5 分钟上手
│   └── troubleshooting.md        # 常见问题排查
├── examples/                     # 示例项目
│   └── url-shortener/            # 完整项目产出示例
├── CONTRIBUTING.md               # 贡献指南
├── README.md                     # 英文
├── README.zh.md                  # 中文
├── README.ja.md                  # 日本語
├── LICENSE                       # MIT
└── .gitignore
```

## 对比

### 为什么不是 Devin？

Devin 是一个超强的单 Agent 开发者，擅长快速写代码。但它只有**一个角色**——没有产品审查、没有安全审计、没有 QA 测试、没有部署回滚。

Rigor 是**12 个角色按标准软件工程流程协作**，交付的是**工程质量**，不只是写代码速度。

### 为什么不是 Cursor？

Cursor 是优秀的 AI 编程助手，辅助**你**写代码。但它不能自主协作——你需要自己决定架构、自己写测试、自己审查。

Rigor 是**自主协作的 AI 团队**——你输入需求，剩下全部交给 AI。

## 任务管理 (Task Management)

### ✏️ 修改任务
任务创建后，如果想纠正或补充描述，**不需要删除任务**：

*   **推荐：追加评论**（Agent 会在约 60 秒后的调度周期自动读取）：
    ```bash
    hermes kanban comment <id> "纠正：不需要按日期排序，只按 Star 数倒序。"
    ```
*   **更新描述**（直接修改任务卡片内容）：
    ```bash
    hermes kanban update <id> --body "新的完整描述..."
    ```

### 🛑 停止任务
如果任务卡死、报错严重或不再需要：

*   **停止 (Block)**（阻止子任务继续执行）：
    ```bash
    hermes kanban block <id> "Cancelled by user"
    ```
*   **重置 (Reset)**（退回到待办状态，适合重试）：
    ```bash
    hermes kanban reset <id>
    ```
*   **归档 (Archive)**（从列表中隐藏，保留历史）：
    ```bash
    hermes kanban archive <id>
    ```

## 知识库

Rigor 包含结构化知识库，用于跨项目经验复用：

- **knowledge-index.json** — 6 条知识条目，含标签、68 个同义词、置信度和相关度规则
- **effectiveness.json** — 追踪每条知识实际防止了多少次问题，含自动衰减规则（30 天未用 → declining、60 天 → stale、180 天 → archived）
- **project-profiles.json** — 根据项目类型和激活角色自动注入相关知识
- **edges.json** — 知识关系图谱（决策 → Bug → 修复 → 模式）

## Roadmap

- [x] 12 角色 SOUL.md + 协作流程
- [x] TDD 优先模式（QA 先写测试）
- [x] 覆盖率门禁（行≥80%、分支≥70%）
- [x] Artifact 版本管理
- [x] 自我修正闭环（自动修复 + 人工升级协议）
- [x] 结构化知识库（索引 + 语义检索 + 衰减机制）
- [x] 项目仪表盘 + 任务状态报告
- [x] 项目复盘 + 历史档案
- [x] 部署回滚协议
- [x] 增量更新模式
- [x] 代码风格统一（ruff / prettier / eslint）
- [ ] 更多垂直领域角色（金融、医疗、法律）
- [ ] 自定义角色创建指南
- [ ] Web Dashboard 集成
- [ ] 多语言 SOUL.md 支持

## 日常维护

### 🧹 一键清理已完成任务
为了保持看板列表整洁，你可以**一键归档**所有 `done` 状态的任务。这会让它们从默认列表中隐藏，但数据保留在数据库中（通过 `--archived` 仍可找回）。

```bash
hermes kanban list --status done | grep -oE 't_[a-f0-9]+' | xargs -I {} hermes kanban archive {}
```

### 📜 查看历史归档
```bash
hermes kanban list --archived
```

---

## 贡献

欢迎贡献！

- **添加新角色**: Fork → 创建 `profiles/<role>/SOUL.md` → PR
- **改进现有角色**: 编辑 `profiles/<role>/SOUL.md` → PR
- **添加知识条目**: 更新 `knowledge-base/` → PR
- **报告 Bug**: Issues 或 PR 都欢迎

## 许可证

MIT — 详见 [LICENSE](LICENSE)

---

⭐ 如果 Rigor 对你有帮助，请给个 ⭐ 鼓励一下！
