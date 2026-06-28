# Rigor Expert Team Profiles

12 个 AI 专家角色，基于 Hermes Agent 的 Profile 系统实现。

## 🏗️ 设计哲学

每个角色的 SOUL.md 遵循统一的设计模式：

```
身份定义 → 核心原则 → 工作流(Observe→Plan→Execute→Verify→Reflexion)
→ 输出规范 → 结构化通信 → 知识沉淀 → 沟通风格
```

### Phase 5: Reflexion（自我反思）

所有执行类角色在完成任务后必须进行 **3 维自我评估**：
- 质量评分（1-10）
- 完整性评分（1-10）  
- 风险评分（1-10）

评分 < 7 时必须主动修正后再提交。

## 👥 角色清单

| 角色 | 类型 | 核心职责 |
|------|------|----------|
| `orchestrator` | 协调层 | 需求分析、任务分解、动态角色激活、自我修正闭环 |
| `product-manager` | 上游 | PRD、验收标准、UAT 验收 |
| `tech-lead` | 上游 | 技术架构、DAG 规划、可行性验证、ADR |
| `backend-engineer` | 执行层 | API、数据库、业务逻辑 |
| `frontend-engineer` | 执行层 | UI、组件、状态管理 |
| `data-scientist` | 执行层 | 数据分析、ML、统计建模 |
| `data-engineer` | 执行层 | 数据管道、向量库、RAG |
| `code-reviewer` | 保障层 | 架构审查、代码审查、多代理辩论仲裁 |
| `security-auditor` | 保障层 | 安全审计（两阶段）、漏洞扫描 |
| `qa-engineer` | 保障层 | TDD 测试用例、自动化测试、质量门禁 |
| `devops-engineer` | 执行层 | CI/CD、容器、基础设施部署 |
| `technical-writer` | 收尾 | 技术文档、API 文档、README |

## 📐 SOUL.md 模板

新角色应基于 `SOUL-TEMPLATE.md` 创建，确保一致性。

```bash
cp profiles/SOUL-TEMPLATE.md profiles/new-role/SOUL.md
# 编辑 SOUL.md 中的占位符
```

## 🔄 角色间协作协议

- **SDD/TDD/契约工作流**: PM 输出 User Story + Acceptance Criteria (Given/When/Then) → QA 基于 AC 生成 BDD 测试和 API 契约测试 → 工程师按测试与契约实现
- **Problem Framing 先行并确认**: Orchestrator 在 PRD/DAG 前写入 `artifacts/orchestrator/problem-frame.md/json`，并取得用户确认；未 `confirmed_by_user=true` 不得创建实现任务
- **AC → 测试映射**: QA 的测试用例必须 1:1 覆盖 PM 交付的所有 AC
- **API 契约门禁**: OpenAPI、后端真实路由、前端真实调用、运行时 smoke 必须一致；优先使用 `rigor contract check`
- **Artifact 传递链**: 每个角色消费上游 artifacts → 产出自身 artifacts
- **结构化通信**: 使用 `kanban_comment` 发送 JSON 格式的结构化消息
- **质量门禁**: Contract Check + QA + Security + Code Reviewer 四道防线
- **Multi-Agent Debate**: 审查分歧时触发三方辩论（engineer + reviewer + tech-lead）
- **自我修正闭环**: 失败自动重试（最多 3 次），超过后触发人工干预

## 🧠 知识系统

| 类型 | 路径 | 触发条件 |
|------|------|----------|
| 架构决策 | `shared/decisions/` | 技术选型、方案对比 |
| 实现模式 | `shared/patterns/` | 好的架构决策、实现模式 |
| 踩坑记录 | `shared/gotchas/` | 审查打回、Bug 发现、UAT 打回 |
| 复盘报告 | `shared/retrospectives/` | 项目完成后自动生成 |
