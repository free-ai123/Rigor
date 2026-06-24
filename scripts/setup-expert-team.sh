#!/bin/bash
# ============================================================
# Hermes Expert Team (Rigor) — 一键部署脚本 (v3.0)
# 兼容 macOS 和 Linux
# ============================================================
set -euo pipefail

HERMES_HOME="${HERMES_HOME:-$HOME/.hermes}"
PROFILES_DIR="$HERMES_HOME/profiles"
CONFIG_FILE="$HERMES_HOME/config.yaml"

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "============================================================"
echo -e "  \033[1;34mHermes Expert Team (Rigor)\033[0m 部署 (v3.0)"
echo -e "============================================================"
echo ""
echo "HERMES_HOME: $HERMES_HOME"
echo "Platform: $(uname -s)"
echo ""

# ----------------------------------------------------------
# 步骤 1: 安装 Profile
# ----------------------------------------------------------
echo -e "[1/4] 安装专家角色 Profile..."

PROFILES=(
    "orchestrator" "product-manager" "tech-lead" "backend-engineer"
    "frontend-engineer" "data-scientist" "data-engineer" "code-reviewer"
    "security-auditor" "qa-engineer" "devops-engineer" "technical-writer"
)

for profile in "${PROFILES[@]}"; do
    profile_dir="$PROFILES_DIR/$profile"
    mkdir -p "$profile_dir/skills" "$profile_dir/memories"
    
    # 复制 SOUL.md 和 config.yaml (使用脚本所在目录相对路径)
    # 注意：setup-expert-team.sh 应该在 profiles/ 同级目录运行，或者在仓库根目录运行
    # 我们假设用户在仓库根目录运行，所以路径是 profiles/$profile/
    SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
    
    if [ -f "$SCRIPT_DIR/profiles/$profile/SOUL.md" ]; then
        cp "$SCRIPT_DIR/profiles/$profile/SOUL.md" "$profile_dir/SOUL.md"
        echo -e "  ✅ ${GREEN}$profile${NC}: SOUL.md 更新"
    elif [ -d "$profile_dir" ]; then
        echo -e "  ⚠️  ${YELLOW}$profile${NC}: SOUL.md 未找到 (跳过)"
    else
        echo -e "  ❌ ${RED}$profile${NC}: 缺少 SOUL.md"
    fi
    
    if [ -f "$SCRIPT_DIR/profiles/$profile/config.yaml" ]; then
        cp "$SCRIPT_DIR/profiles/$profile/config.yaml" "$profile_dir/config.yaml"
    fi
done
echo ""

# ----------------------------------------------------------
# 步骤 2: 配置 Kanban
# ----------------------------------------------------------
echo -e "[2/4] 配置 Kanban..."

kanban_set() {
    local key=$1
    local value=$2
    # 使用 sed 更新配置文件，如果 key 不存在则追加
    if grep -q "$key:" "$CONFIG_FILE" 2>/dev/null; then
        # macOS sed 需要 '' 参数
        if [[ "$OSTYPE" == "darwin"* ]]; then
            sed -i '' "s|^  $key:.*|  $key: $value|" "$CONFIG_FILE"
        else
            sed -i "s|^  $key:.*|  $key: $value|" "$CONFIG_FILE"
        fi
    else
        echo "  kanban:" >> "$CONFIG_FILE"
        echo "    $key: $value" >> "$CONFIG_FILE"
    fi
    echo -e "  ${GREEN}✓${NC} Set $key = $value"
}

kanban_set "kanban.orchestrator_profile" "orchestrator"
kanban_set "kanban.auto_decompose" "true"
kanban_set "kanban.auto_decompose_per_tick" "3"
kanban_set "kanban.dispatch_in_gateway" "true"
kanban_set "kanban.dispatch_interval_seconds" "60"
kanban_set "kanban.failure_limit" "2"
kanban_set "kanban.dispatch_stale_timeout_seconds" "14400"
echo ""

# ----------------------------------------------------------
# 步骤 3: 启动 Gateway
# ----------------------------------------------------------
echo -e "[3/4] 检查/启动 Gateway..."

# macOS 使用 launchctl, Linux 使用 systemd 或后台进程
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "  (macOS 检测到，使用 launchctl 管理)"
    # 检查 launchd 服务状态
    if launchctl list | grep -q "ai.hermes.gateway"; then
        echo -e "  ${GREEN}✅${NC} Hermes Gateway 已加载 (Launchd)"
    else
        echo -e "  ${YELLOW}⚠️${NC} Hermes Gateway 未加载。请运行: ${CYAN}hermes gateway start${NC}"
    fi
else
    # Linux 检查
    if hermes gateway status 2>/dev/null | grep -q "running"; then
        echo -e "  ${GREEN}✅${NC} Hermes Gateway 运行中"
    else
        echo -e "  ${YELLOW}⚠️${NC} Hermes Gateway 未运行。尝试启动..."
        hermes gateway start 2>/dev/null || echo -e "  ${RED}❌ 启动失败，请手动运行 hermes gateway start${NC}"
    fi
fi
echo ""

# ----------------------------------------------------------
# 步骤 4: 部署验证 (更稳健的方式)
# ----------------------------------------------------------
echo -e "[4/4] 部署验证..."

ERRORS=0

# 1. 验证 Profile 目录
for profile in "${PROFILES[@]}"; do
    if [ ! -f "$PROFILES_DIR/$profile/SOUL.md" ]; then
        echo -e "  ${RED}❌${NC} 缺失: $profile/SOUL.md"
        ERRORS=$((ERRORS + 1))
    fi
done
if [ $ERRORS -eq 0 ]; then
    echo -e "  ${GREEN}✅${NC} 12 个 Profile 已正确安装"
fi

# 2. 验证 Kanban 配置 (直接读取文件，不依赖 CLI)
echo ""
if grep -q "auto_decompose: true" "$CONFIG_FILE"; then
    echo -e "  ${GREEN}✅${NC} kanban.auto_decompose = true"
else
    echo -e "  ${RED}❌${NC} kanban.auto_decompose 未配置为 true (请检查 $CONFIG_FILE)"
    ERRORS=$((ERRORS + 1))
fi

if grep -q "orchestrator_profile: orchestrator" "$CONFIG_FILE"; then
    echo -e "  ${GREEN}✅${NC} kanban.orchestrator_profile = orchestrator"
else
    echo -e "  ${RED}❌${NC} kanban.orchestrator_profile 未配置 (请检查 $CONFIG_FILE)"
    ERRORS=$((ERRORS + 1))
fi

echo ""
if [ $ERRORS -eq 0 ]; then
    echo -e "============================================================"
    echo -e "  ${GREEN}🎉 部署成功！一切正常。${NC}"
    echo -e "============================================================"
    echo ""
    echo "接下来你可以："
    echo "  1. hermes kanban create 'Build a URL shortener' --status triage"
    echo "  2. hermes kanban list"
else
    echo -e "============================================================"
    echo -e "  ${RED}⚠️  部署有 $ERRORS 个问题。${NC}"
    echo -e "============================================================"
    echo ""
    echo "请检查上面的错误提示，或查看日志: ~/.hermes/logs/"
fi
