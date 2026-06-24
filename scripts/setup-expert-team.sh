#!/usr/bin/env bash
# ============================================================
# Rigor Installer v4.0 (Professional Edition)
# Usage:
#   ./scripts/setup-expert-team.sh             # 安装/更新
#   ./scripts/setup-expert-team.sh --uninstall # 卸载
#   ./scripts/setup-expert-team.sh --status    # 状态检查
# ============================================================
set -euo pipefail

# --- 颜色定义 ---
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# --- 路径解析 (支持在任何目录下运行) ---
SOURCE="${BASH_SOURCE[0]}"
while [ -h "$SOURCE" ]; do
  DIR="$( cd -P "$( dirname "$SOURCE" )" && pwd )"
  SOURCE="$(readlink "$SOURCE")"
  [[ $SOURCE != /* ]] && SOURCE="$DIR/$SOURCE"
done
REPO_ROOT="$( cd -P "$( dirname "$SOURCE" )/.." && pwd )"

HERMES_HOME="${HERMES_HOME:-$HOME/.hermes}"
PROFILES_DIR="$HERMES_HOME/profiles"
CONFIG_FILE="$HERMES_HOME/config.yaml"

# 核心角色列表
PROFILES=(
    "orchestrator" "product-manager" "tech-lead" "backend-engineer"
    "frontend-engineer" "data-scientist" "data-engineer" "code-reviewer"
    "security-auditor" "qa-engineer" "devops-engineer" "technical-writer"
)

# --- 日志函数 ---
log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[OK]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# --- 检查前提条件 ---
check_prerequisites() {
    if ! command -v hermes &> /dev/null; then
        log_error "Hermes 未安装或未添加到 PATH。请先安装 Hermes Agent。"
        exit 1
    fi

    local hermes_version
    hermes_version=$(hermes --version 2>/dev/null || echo "Unknown")
    log_info "检测到 Hermes 版本: $hermes_version"

    # macOS 内存检查 (建议至少 8GB)
    if [[ "$OSTYPE" == "darwin"* ]]; then
        local mem_mb
        mem_mb=$(sysctl -n hw.memsize 2>/dev/null | awk '{print $1/1024/1024}')
        if (( $(echo "$mem_mb < 8000" | bc -l) )); then
            log_warn "系统内存 < 8GB。运行完整 12 角色团队可能会卡顿，建议使用部分角色模式。"
        fi
    fi
}

# --- 安装逻辑 ---
do_install() {
    check_prerequisites

    log_info "开始安装 Rigor Expert Team..."
    
    # 1. 安装 Profile
    log_info "[1/3] 正在部署专家角色..."
    for profile in "${PROFILES[@]}"; do
        profile_dir="$PROFILES_DIR/$profile"
        mkdir -p "$profile_dir/skills" "$profile_dir/memories"
        
        if [ -f "$REPO_ROOT/profiles/$profile/SOUL.md" ]; then
            cp "$REPO_ROOT/profiles/$profile/SOUL.md" "$profile_dir/SOUL.md"
            log_success "$profile: SOUL.md 已更新"
        else
            log_error "$profile: 找不到源文件 (路径: $REPO_ROOT/profiles/$profile/)"
            exit 1
        fi
        
        if [ -f "$REPO_ROOT/profiles/$profile/config.yaml" ]; then
            cp "$REPO_ROOT/profiles/$profile/config.yaml" "$profile_dir/config.yaml"
        fi
    done

    # 2. 配置 Kanban (带备份)
    log_info "[2/3] 正在配置 Kanban..."
    if [ -f "$CONFIG_FILE" ]; then
        cp "$CONFIG_FILE" "${CONFIG_FILE}.bak.rigor"
        log_info "已备份 config.yaml -> config.yaml.bak.rigor"
    fi

    hermes config set kanban.orchestrator_profile orchestrator
    hermes config set kanban.auto_decompose true
    hermes config set kanban.auto_decompose_per_tick 3
    hermes config set kanban.dispatch_in_gateway true
    hermes config set kanban.dispatch_interval_seconds 60
    log_success "Kanban 配置已写入"

    # 3. 验证
    log_info "[3/3] 正在验证安装..."
    local errors=0
    
    # 验证 Profile
    for profile in "${PROFILES[@]}"; do
        if [ ! -f "$PROFILES_DIR/$profile/SOUL.md" ]; then
            log_error "验证失败：$profile/SOUL.md 不存在"
            errors=$((errors + 1))
        fi
    done

    # 验证配置
    if grep -q "auto_decompose: true" "$CONFIG_FILE" 2>/dev/null; then
        log_success "配置验证通过：auto_decompose 已开启"
    else
        log_warn "配置验证警告：auto_decompose 可能未正确写入，请检查 config.yaml"
    fi

    if [ $errors -eq 0 ]; then
        echo ""
        echo -e "${GREEN}============================================================${NC}"
        echo -e "${GREEN}  🎉 Rigor 安装成功！${NC}"
        echo -e "${GREEN}============================================================${NC}"
        echo ""
        echo "  💡 使用提示:"
        echo "    - 启动任务：hermes kanban create 'Build a URL shortener' --triage"
        echo "    - 查看进度：hermes kanban list"
        echo "    - 卸载软件：bash scripts/setup-expert-team.sh --uninstall"
        echo ""
    else
        log_error "安装完成但有 $errors 个错误，请检查上述日志。"
        exit 1
    fi
}

# --- 卸载逻辑 ---
do_uninstall() {
    log_warn "即将卸载 Rigor Expert Team。"
    echo -e "${YELLOW}此操作将删除以下 Profile 并还原 Kanban 配置:${NC}"
    for profile in "${PROFILES[@]}"; do
        echo "  - $PROFILES_DIR/$profile"
    done
    
    read -p "是否继续？(输入 YES 确认): " confirm
    if [ "$confirm" != "YES" ]; then
        log_info "操作已取消。"
        exit 0
    fi

    log_info "开始卸载..."

    # 1. 删除 Profile
    for profile in "${PROFILES[@]}"; do
        profile_dir="$PROFILES_DIR/$profile"
        if [ -d "$profile_dir" ]; then
            rm -rf "$profile_dir"
            log_success "$profile 已删除"
        else
            log_warn "$profile 不存在，跳过"
        fi
    done

    # 2. 还原配置 (如果存在备份)
    if [ -f "${CONFIG_FILE}.bak.rigor" ]; then
        cp "${CONFIG_FILE}.bak.rigor" "$CONFIG_FILE"
        rm -f "${CONFIG_FILE}.bak.rigor"
        log_success "配置已还原为安装前的状态"
    else
        log_warn "未找到配置备份，请手动删除 config.yaml 中的 kanban 部分"
        # 尝试自动清理 kanban 键值
        if command -v sed &> /dev/null; then
             if [[ "$OSTYPE" == "darwin"* ]]; then
                sed -i '' '/^kanban:/,/^[^ ]/d' "$CONFIG_FILE" 2>/dev/null || true
             else
                sed -i '/^kanban:/,/^[^ ]/d' "$CONFIG_FILE" 2>/dev/null || true
             fi
             log_info "已尝试自动清理 kanban 配置块"
        fi
    fi

    echo ""
    echo -e "${YELLOW}============================================================${NC}"
    echo -e "${YELLOW}  🗑️ Rigor 已卸载${NC}"
    echo -e "${YELLOW}============================================================${NC}"
    echo ""
    log_info "注意：Gateway 服务未停止，如需清理请手动运行 'hermes gateway stop'"
}

# --- 状态检查 ---
do_status() {
    log_info "Rigor 系统状态检查..."
    
    local installed=0
    local missing=0
    
    for profile in "${PROFILES[@]}"; do
        if [ -f "$PROFILES_DIR/$profile/SOUL.md" ]; then
            installed=$((installed + 1))
        else
            missing=$((missing + 1))
        fi
    done

    echo "  Profile 状态: $installed 已安装 / $missing 缺失"
    
    if grep -q "auto_decompose: true" "$CONFIG_FILE" 2>/dev/null; then
        echo "  Kanban 状态: ✅ 已启用"
    else
        echo "  Kanban 状态: ❌ 未启用"
    fi
}

# --- 入口 ---
case "${1:-}" in
    --uninstall)
        do_uninstall
        ;;
    --status)
        do_status
        ;;
    *)
        do_install
        ;;
esac
