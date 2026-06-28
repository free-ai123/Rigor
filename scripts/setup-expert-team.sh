#!/usr/bin/env bash
# ============================================================
# Rigor Installer v5.0 (Smart Edition)
#
# Features:
#   - Auto-detects Hermes, offers one-tap install if missing
#   - Reuses existing model config or prompts for API Key only
#   - Reuses existing profiles or creates new ones
#   - Auto-configures Kanban for multi-agent collaboration
#   - Runs a smoke test to verify everything works
#
# Usage:
#   ./scripts/setup-expert-team.sh             # Install / Update
#   ./scripts/setup-expert-team.sh --uninstall # Uninstall
#   ./scripts/setup-expert-team.sh --status    # Status check
# ============================================================
set -uo pipefail

# --- Colors ---
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

# --- Path Resolution ---
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

# --- Core Roles ---
ROLES=(
    "orchestrator" "product-manager" "tech-lead" "backend-engineer"
    "frontend-engineer" "data-scientist" "data-engineer" "code-reviewer"
    "security-auditor" "qa-engineer" "devops-engineer" "technical-writer"
)

# --- Model Presets (best practices built-in) ---
# Keep this Bash 3 compatible for macOS' system /bin/bash.
model_preset_for_choice() {
    case "$1" in
        1) printf "%s\n" "anthropic/claude-sonnet-4|anthropic|ANTHROPIC_API_KEY|Anthropic" ;;
        2) printf "%s\n" "openai/gpt-4o|openai|OPENAI_API_KEY|OpenAI" ;;
        3) printf "%s\n" "deepseek/deepseek-chat|deepseek|DEEPSEEK_API_KEY|DeepSeek" ;;
        4) printf "%s\n" "alibaba/qwen3.6-plus|alibaba|DASHSCOPE_API_KEY|Alibaba Qwen" ;;
        *) return 1 ;;
    esac
}

# --- Logging ---
log_info()    { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[OK]${NC}   $1"; }
log_warn()    { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error()   { echo -e "${RED}[ERROR]${NC} $1"; }
log_step()    { echo -e "\n${CYAN}${BOLD}━━━ $1 ━━━${NC}"; }

# --- Prompt Helper ---
prompt_yes_no() {
    local prompt="$1"
    local default="${2:-Y}"
    local input
    if [ "$default" = "Y" ]; then
        echo -ne "  ${BOLD}${prompt} [Y/n]:${NC} "
    else
        echo -ne "  ${BOLD}${prompt} [y/N]:${NC} "
    fi
    read -r input
    if [ -z "$input" ]; then
        [ "$default" = "Y" ] && return 0 || return 1
    fi
    case "$input" in
        [yY][eE][sS]|[yY]) return 0 ;;
        *) return 1 ;;
    esac
}

get_existing_api_key() {
    local env_var="$1"
    local env_file="$HERMES_HOME/.env"
    local value=""

    value=$(printenv "$env_var" 2>/dev/null || true)
    if [ -n "$value" ]; then
        printf "%s\n" "$value"
        return 0
    fi

    if [ -f "$env_file" ]; then
        value=$(grep "^${env_var}=" "$env_file" 2>/dev/null | tail -1 | sed "s|^${env_var}=||" || true)
        if [ -n "$value" ]; then
            printf "%s\n" "$value"
        fi
    fi
}

is_configured_value() {
    local value
    value=$(printf "%s" "${1:-}" | tr '[:upper:]' '[:lower:]')
    case "$value" in
        ""|"not set"|"none"|"null"|"unknown")
            return 1
            ;;
        *)
            return 0
            ;;
    esac
}

read_config_value_from_file() {
    local key="$1"
    if [ ! -f "$CONFIG_FILE" ]; then
        return 0
    fi
    python3 - "$CONFIG_FILE" "$key" <<'PY' 2>/dev/null || true
import sys
from pathlib import Path

path = Path(sys.argv[1])
wanted = sys.argv[2]
values = {}
stack = []

for raw_line in path.read_text(encoding="utf-8", errors="replace").splitlines():
    if not raw_line.strip() or raw_line.lstrip().startswith("#"):
        continue
    if raw_line.lstrip().startswith("- "):
        continue
    indent = len(raw_line) - len(raw_line.lstrip(" "))
    stripped = raw_line.strip()
    if ":" not in stripped:
        continue
    key, value = stripped.split(":", 1)
    key = key.strip()
    value = value.strip()
    while stack and stack[-1][0] >= indent:
        stack.pop()
    current_path = ".".join([item[1] for item in stack] + [key])
    if value:
        values[current_path] = value.strip("'\"")
    else:
        stack.append((indent, key))

print(values.get(wanted, ""))
PY
}

hermes_config_get() {
    local key="$1"
    local value
    value=$(hermes config get "$key" 2>/dev/null || true)
    if is_configured_value "$value"; then
        printf "%s\n" "$value"
        return 0
    fi
    read_config_value_from_file "$key"
}

is_enabled_value() {
    local value
    value=$(printf "%s" "${1:-}" | tr '[:upper:]' '[:lower:]')
    case "$value" in
        true|yes|1|on)
            return 0
            ;;
        *)
            return 1
            ;;
    esac
}

# ============================================================
# PHASE 1: Hermes Environment Detection
# ============================================================
ensure_hermes() {
    log_step "Phase 1: Hermes Environment Detection"

    if command -v hermes &> /dev/null; then
        local hermes_version
        hermes_version=$(hermes --version 2>/dev/null || echo "Unknown")
        log_success "Hermes detected: $hermes_version"
        
        # Run doctor check
        if hermes doctor &>/dev/null; then
            log_success "Hermes health check passed"
        else
            log_warn "Hermes doctor reported issues. You may need to run 'hermes setup'."
        fi
    else
        log_warn "Hermes Agent is not installed."
        echo -e "  ${NC}Rigor requires Hermes Agent to run the multi-agent team."
        echo ""
        if prompt_yes_no "Install Hermes Agent now?" "Y"; then
            log_info "Installing Hermes Agent..."
            echo ""
            curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash
            echo ""
            
            # Reload shell
            if [ -f "$HOME/.bashrc" ]; then
                source "$HOME/.bashrc" 2>/dev/null || true
            elif [ -f "$HOME/.zshrc" ]; then
                source "$HOME/.zshrc" 2>/dev/null || true
            fi

            if command -v hermes &> /dev/null; then
                log_success "Hermes installed successfully!"
                # Run initial setup if needed
                if [ ! -f "$CONFIG_FILE" ]; then
                    log_info "Running initial Hermes setup..."
                    hermes setup --non-interactive 2>/dev/null || log_warn "Please run 'hermes setup' manually to configure your model."
                fi
            else
                log_error "Hermes installation failed. Please install manually: https://hermes-agent.nousresearch.com/docs/"
                exit 1
            fi
        else
            log_error "Installation cancelled. Rigor cannot run without Hermes."
            exit 1
        fi
    fi
}

# ============================================================
# PHASE 2: Smart Model Configuration
# ============================================================
configure_model() {
    log_step "Phase 2: Model Configuration"

    # Detect current model
    local current_model current_provider
    current_model=$(hermes_config_get model.default)
    current_provider=$(hermes_config_get model.provider)

    if is_configured_value "$current_model"; then
        log_success "Current default model: ${BOLD}${current_model}${NC}"
        echo "  Rigor will use this model for all expert roles."
        echo ""
        if prompt_yes_no "Reuse this model?" "Y"; then
            log_success "Will reuse: $current_model"
            return 0
        fi
    else
        log_warn "No default model configured yet."
    fi

    echo ""
    printf "  %bChoose a model for the Rigor team:%b\n" "$BOLD" "$NC"
    echo ""
    echo "  1) Claude Sonnet 4  (Recommended for coding)"
    echo "  2) GPT-4o           (Great all-rounder)"
    echo "  3) DeepSeek Chat    (Cost-effective)"
    echo "  4) Qwen 3.6 Plus    (Strong Chinese support)"
    echo ""
    echo -ne "  ${BOLD}Enter choice [1-4, default 1]:${NC} "
    read -r choice || choice=""
    choice="${choice:-1}"

    local preset
    preset=$(model_preset_for_choice "$choice" || true)
    if [ -z "$preset" ]; then
        log_warn "Invalid choice '$choice'. Using default (Claude Sonnet 4)."
        choice=1
        preset=$(model_preset_for_choice "$choice")
    fi

    IFS='|' read -r model_id provider env_var provider_name <<< "$preset"

    echo ""
    local api_key existing_api_key
    existing_api_key=$(get_existing_api_key "$env_var")
    if [ -n "$existing_api_key" ] && prompt_yes_no "Reuse existing ${env_var} from environment or ~/.hermes/.env?" "Y"; then
        api_key="$existing_api_key"
    else
        echo -ne "  ${BOLD}Enter your ${provider_name} API Key:${NC} "
        read -r api_key || api_key=""
    fi
    
    if [ -z "$api_key" ]; then
        log_error "API Key cannot be empty."
        exit 1
    fi

    log_info "Configuring model..."
    
    # Set model and provider
    hermes config set model.default "$model_id"
    hermes config set model.provider "$provider"
    
    # Store API key in .env
    local env_file="$HERMES_HOME/.env"
    mkdir -p "$HERMES_HOME"
    touch "$env_file"
    if ! grep -q "^${env_var}=" "$env_file" 2>/dev/null; then
        echo "${env_var}=${api_key}" >> "$env_file"
    else
        sed -i.bak "s|^${env_var}=.*|${env_var}=${api_key}|" "$env_file"
        rm -f "${env_file}.bak"
    fi

    log_success "Model configured: $model_id ($provider_name)"
}

# ============================================================
# PHASE 3: Profile Deployment (Reuse or Create)
# ============================================================
deploy_profiles() {
    log_step "Phase 3: Deploying Expert Roles"

    local created=0 updated=0 skipped=0

    for role in "${ROLES[@]}"; do
        local profile_dir="$PROFILES_DIR/$role"
        local soul_src="$REPO_ROOT/profiles/$role/SOUL.md"
        local config_src="$REPO_ROOT/profiles/$role/config.yaml"

        if [ -d "$profile_dir" ] && [ -f "$profile_dir/SOUL.md" ]; then
            # Profile exists - update
            if [ -f "$soul_src" ]; then
                cp "$soul_src" "$profile_dir/SOUL.md"
                sync_profile_runtime_config "$profile_dir" "$config_src"
                log_success "$role: updated (existing profile reused)"
                updated=$((updated + 1))
            else
                log_warn "$role: SOUL.md source not found, skipping"
                skipped=$((skipped + 1))
            fi
        else
            # Create new profile
            mkdir -p "$profile_dir/skills" "$profile_dir/memories"
            if [ -f "$soul_src" ]; then
                cp "$soul_src" "$profile_dir/SOUL.md"
                log_success "$role: created"
            else
                log_error "$role: SOUL.md source not found"
                skipped=$((skipped + 1))
                continue
            fi
            sync_profile_runtime_config "$profile_dir" "$config_src"
            created=$((created + 1))
        fi
    done

    echo ""
    echo "  Summary: ${created} created, ${updated} updated, ${skipped} skipped"
}

sync_profile_runtime_config() {
    local profile_dir="$1"
    local fallback_config="$2"

    mkdir -p "$profile_dir"

    # Profiles have their own HERMES_HOME. Copy the user's working Hermes
    # runtime config/auth so profiles reuse the already configured provider,
    # model, login, custom endpoints, and API keys. SOUL.md remains role-specific.
    if [ -f "$CONFIG_FILE" ]; then
        cp "$CONFIG_FILE" "$profile_dir/config.yaml"
    elif [ -f "$fallback_config" ]; then
        cp "$fallback_config" "$profile_dir/config.yaml"
    fi

    if [ -f "$HERMES_HOME/.env" ]; then
        cp "$HERMES_HOME/.env" "$profile_dir/.env"
        chmod 600 "$profile_dir/.env" 2>/dev/null || true
    fi

    if [ -f "$HERMES_HOME/auth.json" ]; then
        cp "$HERMES_HOME/auth.json" "$profile_dir/auth.json"
        chmod 600 "$profile_dir/auth.json" 2>/dev/null || true
    fi
}

# ============================================================
# PHASE 4: Kanban Configuration
# ============================================================
configure_kanban() {
    log_step "Phase 4: Configuring Kanban Board"

    if [ -f "$CONFIG_FILE" ]; then
        cp "$CONFIG_FILE" "${CONFIG_FILE}.bak.rigor"
        log_info "Backed up config.yaml"
    fi

    hermes config set kanban.orchestrator_profile orchestrator
    hermes config set kanban.auto_decompose true
    hermes config set kanban.auto_decompose_per_tick 3
    hermes config set kanban.dispatch_in_gateway true
    hermes config set kanban.dispatch_interval_seconds 60
    
    log_success "Kanban configured for multi-agent collaboration"

    # Initialize kanban board
    hermes kanban init 2>/dev/null || log_warn "Kanban board already initialized"
}

# ============================================================
# PHASE 5: Smoke Test
# ============================================================
run_smoke_test() {
    log_step "Phase 5: System Verification"

    log_info "Running health check..."
    
    local errors=0

    # Verify profiles
    for role in "${ROLES[@]}"; do
        if [ ! -f "$PROFILES_DIR/$role/SOUL.md" ]; then
            log_error "Missing: $role/SOUL.md"
            errors=$((errors + 1))
        fi
    done

    # Verify kanban config
    local auto_decompose
    auto_decompose=$(hermes_config_get kanban.auto_decompose)
    if is_enabled_value "$auto_decompose"; then
        log_success "Kanban: auto_decompose enabled"
    else
        log_warn "Kanban: auto_decompose may not be set correctly"
    fi

    # Quick model verification
    local model
    model=$(hermes_config_get model.default)
    if is_configured_value "$model"; then
        log_success "Model: $model"
    else
        log_warn "Model: not configured"
        errors=$((errors + 1))
    fi

    return $errors
}

# ============================================================
# Main Install Flow
# ============================================================
do_install() {
    echo ""
    echo -e "${GREEN}${BOLD}╔══════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}${BOLD}║     🤖  Rigor Smart Installer v5.0         ║${NC}"
    echo -e "${GREEN}${BOLD}║     12-Role AI Engineering Team            ║${NC}"
    echo -e "${GREEN}${BOLD}╚══════════════════════════════════════════════╝${NC}"
    echo ""

    ensure_hermes
    configure_model
    deploy_profiles
    configure_kanban
    run_smoke_test

    if [ $? -eq 0 ]; then
        echo ""
        echo -e "${GREEN}${BOLD}============================================================${NC}"
        echo -e "${GREEN}${BOLD}  🎉  Rigor Expert Team deployed successfully!${NC}"
        echo -e "${GREEN}${BOLD}============================================================${NC}"
        echo ""
        echo "  💡 Quick Start:"
        echo "    hermes kanban create 'Build a URL shortener' --triage"
        echo "    hermes kanban list"
        echo ""
    else
        log_error "Deployment completed with errors. Please review the log above."
        exit 1
    fi
}

# ============================================================
# Uninstall
# ============================================================
do_uninstall() {
    log_warn "Uninstalling Rigor Expert Team."
    echo -e "  ${YELLOW}This will delete the following profiles:${NC}"
    for role in "${ROLES[@]}"; do
        echo "    - $PROFILES_DIR/$role"
    done
    echo ""
    
    read -p "  Type YES to confirm: " confirm
    if [ "$confirm" != "YES" ]; then
        log_info "Cancelled."
        exit 0
    fi

    log_info "Uninstalling..."

    for role in "${ROLES[@]}"; do
        if [ -d "$PROFILES_DIR/$role" ]; then
            rm -rf "$PROFILES_DIR/$role"
            log_success "$role: removed"
        fi
    done

    if [ -f "${CONFIG_FILE}.bak.rigor" ]; then
        cp "${CONFIG_FILE}.bak.rigor" "$CONFIG_FILE"
        rm -f "${CONFIG_FILE}.bak.rigor"
        log_success "Config restored from backup"
    fi

    echo ""
    echo -e "${YELLOW}============================================================${NC}"
    echo -e "${YELLOW}  🗑️  Rigor uninstalled${NC}"
    echo -e "${YELLOW}============================================================${NC}"
}

# ============================================================
# Status
# ============================================================
do_status() {
    log_info "Rigor Status Check"
    echo ""

    # Hermes
    if command -v hermes &> /dev/null; then
        log_success "Hermes: $(hermes --version 2>/dev/null)"
    else
        log_error "Hermes: not installed"
    fi

    # Model
    local model
    model=$(hermes_config_get model.default)
    if is_configured_value "$model"; then
        log_success "Model: $model"
    else
        log_warn "Model: not configured"
    fi

    # Profiles
    local installed=0 missing=0
    for role in "${ROLES[@]}"; do
        if [ -f "$PROFILES_DIR/$role/SOUL.md" ]; then
            installed=$((installed + 1))
        else
            missing=$((missing + 1))
        fi
    done
    echo "  Profiles: $installed installed / $missing missing"

    # Kanban
    if grep -q "auto_decompose: true" "$CONFIG_FILE" 2>/dev/null; then
        log_success "Kanban: enabled"
    else
        log_warn "Kanban: not enabled"
    fi
}

# --- Entry ---
case "${1:-}" in
    --uninstall) do_uninstall ;;
    --status)    do_status ;;
    *)           do_install ;;
esac
