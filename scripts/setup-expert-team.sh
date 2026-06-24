#!/bin/bash
# ============================================================
# Hermes 多角色专家团 — 一键部署脚本
# 用法: bash setup-expert-team.sh
# 版本: 2.0 (12 roles, with verification)
# ============================================================
set -e

HERMES_HOME="${HERMES_HOME:-$HOME/.hermes}"
PROFILES_DIR="$HERMES_HOME/profiles"

echo "============================================================"
echo "  Hermes 多角色专家团 部署 (v2.0)"
echo "============================================================"
echo ""
echo "HERMES_HOME: $HERMES_HOME"
echo "Profiles 目录: $PROFILES_DIR"
echo ""

# ---- 步骤 1: 安装 Profile 角色 ----
echo "[1/4] 安装专家角色 Profile..."

PROFILES=(
    "orchestrator"
    "product-manager"
    "tech-lead"
    "backend-engineer"
    "frontend-engineer"
    "data-scientist"
    "data-engineer"
    "code-reviewer"
    "security-auditor"
    "qa-engineer"
    "devops-engineer"
    "technical-writer"
)

INSTALLED=0
for profile in "${PROFILES[@]}"; do
    profile_dir="$PROFILES_DIR/$profile"
    if [ -d "$profile_dir" ]; then
        echo "  ♻️  $profile (已存在，更新 SOUL.md 和 config.yaml)"
    else
        echo "  📦 创建 $profile..."
        mkdir -p "$profile_dir/skills" "$profile_dir/memories"
    fi
    # 复制 SOUL.md
    if [ -f "profiles/$profile/SOUL.md" ]; then
        cp "profiles/$profile/SOUL.md" "$profile_dir/SOUL.md"
    fi
    # 复制 config.yaml
    if [ -f "profiles/$profile/config.yaml" ]; then
        cp "profiles/$profile/config.yaml" "$profile_dir/config.yaml"
    fi
    INSTALLED=$((INSTALLED + 1))
done
echo "  ✅ $INSTALLED 个 Profile 已安装/更新"

# ---- 步骤 2: 配置 Kanban ----
echo ""
echo "[2/4] 配置 Kanban..."

hermes config set kanban.orchestrator_profile orchestrator 2>/dev/null || true
hermes config set kanban.auto_decompose true 2>/dev/null || true
hermes config set kanban.auto_decompose_per_tick 3 2>/dev/null || true
hermes config set kanban.dispatch_in_gateway true 2>/dev/null || true
hermes config set kanban.dispatch_interval_seconds 60 2>/dev/null || true
hermes config set kanban.failure_limit 2 2>/dev/null || true
hermes config set kanban.dispatch_stale_timeout_seconds 14400 2>/dev/null || true

echo "  ✅ orchestrator_profile: orchestrator"
echo "  ✅ auto_decompose: true"
echo "  ✅ dispatch_interval: 60s"

# ---- 步骤 3: 启动 Gateway ----
echo ""
echo "[3/4] 启动专家 Gateway..."
echo "（每个角色一个独立 Gateway 进程，内存预算 ~3.5GB）"
echo ""

RUNNING=0
FAILED=0
for profile in "${PROFILES[@]}"; do
    if hermes gateway status -p "$profile" 2>/dev/null | grep -q "running"; then
        echo "  ✅ $profile (已在运行)"
        RUNNING=$((RUNNING + 1))
    else
        echo "  🚀 启动 $profile..."
        if hermes gateway start -p "$profile" 2>/dev/null; then
            echo "    → $profile 已启动"
            RUNNING=$((RUNNING + 1))
        else
            echo "    ❌ $profile 启动失败（检查 config.yaml 和端口占用）"
            FAILED=$((FAILED + 1))
        fi
    fi
done

echo ""
echo "  Gateway 状态: $RUNNING 运行中, $FAILED 失败"

# ---- 步骤 4: 部署验证 ----
echo ""
echo "[4/4] 部署验证..."
echo ""

PASS=0
FAIL=0

# 检查 1: 所有 Profile 目录存在
for profile in "${PROFILES[@]}"; do
    if [ -d "$PROFILES_DIR/$profile" ] && [ -f "$PROFILES_DIR/$profile/SOUL.md" ]; then
        PASS=$((PASS + 1))
    else
        echo "  ❌ $profile: SOUL.md 缺失"
        FAIL=$((FAIL + 1))
    fi
done
echo "  ✅ Profile 目录: $((PASS - FAIL))/$((PASS)) 通过"

# 检查 2: Kanban 配置
ORCHESTRATOR_PROFILE=$(hermes config get kanban.orchestrator_profile 2>/dev/null || echo "")
AUTO_DECOMPOSE=$(hermes config get kanban.auto_decompose 2>/dev/null || echo "")

if [ "$ORCHESTRATOR_PROFILE" = "orchestrator" ]; then
    echo "  ✅ kanban.orchestrator_profile = orchestrator"
else
    echo "  ❌ kanban.orchestrator_profile = '$ORCHESTRATOR_PROFILE' (期望 'orchestrator')"
fi

if [ "$AUTO_DECOMPOSE" = "true" ]; then
    echo "  ✅ kanban.auto_decompose = true"
else
    echo "  ❌ kanban.auto_decompose = '$AUTO_DECOMPOSE' (期望 'true')"
fi

# 检查 3: Gateway 状态
echo ""
GW_RUNNING=$(hermes gateway status 2>/dev/null | grep -c "running" || echo "0")
echo "  Gateway 运行中: $GW_RUNNING / ${#PROFILES[@]}"

if [ "$GW_RUNNING" -ge "$(( ${#PROFILES[@]} / 2 ))" ]; then
    echo "  ✅ 超过半数 Gateway 正常运行"
else
    echo "  ⚠️  运行中的 Gateway 不足半数，请检查日志"
fi

# ---- 完成 ----
echo ""
echo "============================================================"
echo "  部署完成！"
echo "============================================================"
echo ""
echo "专家团角色列表 (12 个):"
echo "  🧠 orchestrator      — 中枢调度（任务分解、路由、进度跟踪）"
echo "  📋 product-manager   — 产品经理（需求分析、PRD、UAT验收）"
echo "  🏗️  tech-lead         — 技术负责人（架构设计、技术选型、DAG规划）"
echo "  💻 backend-engineer  — 后端工程师（API、数据库、服务逻辑）"
echo "  🎨 frontend-engineer — 前端工程师（UI组件、交互、状态管理）"
echo "  📊 data-scientist    — 数据科学家（数据分析、ML、统计建模）"
echo "  🔧 data-engineer     — 数据工程师（数据管道、向量库、RAG管线）"
echo "  🔍 code-reviewer     — 代码审查（架构审查、代码审查）"
echo "  🛡️  security-auditor  — 安全审计（两阶段安全审查、漏洞扫描）"
echo "  🧪 qa-engineer       — QA工程师（测试设计、自动化测试）"
echo "  🔧 devops-engineer   — 运维工程师（CI/CD、容器化、部署）"
echo "  📝 technical-writer  — 技术文档（README、API文档、Changelog）"
echo ""
echo "使用方法:"
echo "  1. 通过 orchestrator 创建需求:"
echo "     hermes -p orchestrator '帮我做一个短链服务'"
echo "  2. 或者直接在 Kanban 创建 triage 任务:"
echo "     hermes kanban create '做一个XXX' --status triage"
echo "     → 自动触发 orchestrator 拆解为 DAG 任务链"
echo ""
echo "查看状态:"
echo "  hermes kanban list              # 查看所有任务"
echo "  hermes kanban show <id> --tree  # 查看任务依赖图"
echo "  hermes gateway status           # 查看 Gateway 状态"
echo ""
echo "管理 Gateway:"
echo "  hermes gateway start -p <profile>  # 启动指定角色"
echo "  hermes gateway stop -p <profile>   # 停止指定角色"
echo ""
