#!/usr/bin/env bash
# ============================================================
# Rigor Monitor v1.0 - 实时监控面板 + 成本追踪
#
# Usage:
#   ./scripts/monitor.sh              # 实时仪表盘模式
#   ./scripts/monitor.sh --cost       # 成本报告模式
#   ./scripts/monitor.sh --budget 50  # 设置预算上限 ($)
#   ./scripts/monitor.sh --status     # 一次性状态快照
# ============================================================
set -uo pipefail

# --- Colors & Styles ---
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
BOLD='\033[1m'
DIM='\033[2m'
NC='\033[0m'

# --- Paths ---
HERMES_HOME="${HERMES_HOME:-$HOME/.hermes}"
PROFILES_DIR="$HERMES_HOME/profiles"
LOG_DIR="$HERMES_HOME/logs"
BUDGET_FILE="$HERMES_HOME/.rigor_budget"

# --- Rigor Roles ---
ROLES=(
    "orchestrator" "product-manager" "tech-lead" "backend-engineer"
    "frontend-engineer" "data-scientist" "data-engineer" "code-reviewer"
    "security-auditor" "qa-engineer" "devops-engineer" "technical-writer"
)

ROLE_ICONS=(
    "🎯" "📋" "🏗️" "⚙️"
    "🎨" "📊" "🔧" "🔍"
    "🛡️" "✅" "🚀" "📝"
)

# --- Utility Functions ---
clear_screen() { clear; }
move_cursor() { tput cup "$1" "$2"; }
hide_cursor() { tput civis; }
show_cursor() { tput cnorm; }

print_header() {
    echo -e "${CYAN}${BOLD}╔══════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}${BOLD}║${NC}  ${WHITE}${BOLD}🤖  Rigor Monitor - Real-time Dashboard            ${CYAN}${BOLD}║${NC}"
    echo -e "${CYAN}${BOLD}╚══════════════════════════════════════════════════════════╝${NC}"
}

print_status_icon() {
    local status="$1"
    case "$status" in
        active|running|working) echo -e "${GREEN}●${NC}" ;;
        idle|ready) echo -e "${BLUE}○${NC}" ;;
        error|failed) echo -e "${RED}✗${NC}" ;;
        paused) echo -e "${YELLOW}⏸${NC}" ;;
        *) echo -e "${DIM}○${NC}" ;;
    esac
}

print_bar() {
    local value="$1" max="$2" width="${3:-30}"
    local filled=$(( value * width / (max + 1) ))
    local empty=$(( width - filled ))
    local bar=""
    for ((i=0; i<filled; i++)); do bar+="█"; done
    for ((i=0; i<empty; i++)); do bar+="░"; done
    echo -ne "${GREEN}${bar}${NC}"
}

# --- Core Functions ---

get_role_status() {
    local role="$1"
    local profile_dir="$PROFILES_DIR/$role"

    if [ ! -d "$profile_dir" ]; then
        echo "missing"
        return
    fi

    # Check for active sessions
    local sessions_dir="$profile_dir/sessions"
    if [ -d "$sessions_dir" ]; then
        local active_sessions
        active_sessions=$(ls -t "$sessions_dir" 2>/dev/null | head -1)
        if [ -n "$active_sessions" ]; then
            local last_mod
            last_mod=$(stat -c %Y "$sessions_dir/$active_sessions" 2>/dev/null || stat -f %m "$sessions_dir/$active_sessions" 2>/dev/null || echo 0)
            local now
            now=$(date +%s)
            local diff=$(( now - last_mod ))
            if [ "$diff" -lt 60 ]; then
                echo "active"
                return
            elif [ "$diff" -lt 300 ]; then
                echo "idle"
                return
            fi
        fi
    fi

    # Check logs for errors
    if [ -f "$LOG_DIR/$role.log" ] || [ -f "$LOG_DIR/gateway.log" ]; then
        if tail -50 "$LOG_DIR/gateway.log" 2>/dev/null | grep -qi "error.*$role\|$role.*error"; then
            echo "error"
            return
        fi
    fi

    echo "ready"
}

get_kanban_summary() {
    local kanban_data
    kanban_data=$(hermes kanban list --no-color 2>/dev/null || echo "")

    if [ -z "$kanban_data" ]; then
        echo "0|0|0|0|0"
        return
    fi

    local total=0 todo=0 in_progress=0 review=0 done_count=0

    while IFS= read -r line; do
        total=$((total + 1))
        if echo "$line" | grep -qi "todo\|backlog"; then
            todo=$((todo + 1))
        elif echo "$line" | grep -qi "progress\|doing"; then
            in_progress=$((in_progress + 1))
        elif echo "$line" | grep -qi "review\|blocked"; then
            review=$((review + 1))
        elif echo "$line" | grep -qi "done\|complete"; then
            done_count=$((done_count + 1))
        fi
    done <<< "$kanban_data"

    echo "${total}|${todo}|${in_progress}|${review}|${done_count}"
}

get_token_usage() {
    local total_input=0 total_output=0

    # Try hermes insights first
    local insights
    insights=$(hermes insights --days 1 --json 2>/dev/null || echo "")
    
    if [ -n "$insights" ]; then
        # Parse JSON if available
        total_input=$(echo "$insights" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('total_input_tokens',0))" 2>/dev/null || echo 0)
        total_output=$(echo "$insights" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('total_output_tokens',0))" 2>/dev/null || echo 0)
    fi

    # Fallback: estimate from log files
    if [ "$total_input" = "0" ] && [ "$total_output" = "0" ] && [ -d "$LOG_DIR" ]; then
        local log_size
        log_size=$(du -sk "$LOG_DIR" 2>/dev/null | cut -f1 || echo 0)
        # Rough estimate: ~1000 tokens per KB of logs
        total_output=$(( log_size * 1000 / 4 ))
    fi

    echo "${total_input}|${total_output}"
}

get_cost_estimate() {
    local input_tokens="$1" output_tokens="$2"
    # Default: Claude Sonnet 4 pricing (approximate)
    # Input: $3/MTok, Output: $15/MTok
    local cost_input=$(python3 -c "print(f'{$input_tokens * 3 / 1000000:.4f}')" 2>/dev/null || echo "0.00")
    local cost_output=$(python3 -c "print(f'{$output_tokens * 15 / 1000000:.4f}')" 2>/dev/null || echo "0.00")
    local total=$(python3 -c "print(f'{$cost_input + $cost_output:.4f}')" 2>/dev/null || echo "0.00")
    
    echo "${cost_input}|${cost_output}|${total}"
}

get_budget() {
    if [ -f "$BUDGET_FILE" ]; then
        cat "$BUDGET_FILE"
    else
        echo "0"
    fi
}

set_budget() {
    local amount="$1"
    echo "$amount" > "$BUDGET_FILE"
}

# --- Dashboard Mode ---
run_dashboard() {
    hide_cursor
    trap 'show_cursor; exit' INT TERM

    local budget
    budget=$(get_budget)

    while true; do
        clear_screen
        print_header
        echo ""

        # --- System Health ---
        echo -e "${BOLD}${WHITE}System Health${NC}"
        echo -e "${DIM}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        
        local hermes_status="Unknown"
        if command -v hermes &>/dev/null; then
            hermes_status=$(hermes --version 2>/dev/null | head -1 || echo "Running")
        fi
        echo -e "  Hermes:     ${GREEN}●${NC} $hermes_status"

        local kanban_status
        if grep -q "dispatch_in_gateway: true" "$HERMES_HOME/config.yaml" 2>/dev/null; then
            kanban_status="${GREEN}Enabled${NC}"
        else
            kanban_status="${RED}Disabled${NC}"
        fi
        echo -e "  Kanban:     $kanban_status"

        local gateway_status
        if pgrep -f "hermes.*gateway" &>/dev/null || pgrep -f "hermes.*run" &>/dev/null; then
            gateway_status="${GREEN}Running${NC}"
        else
            gateway_status="${YELLOW}Stopped${NC}"
        fi
        echo -e "  Gateway:    $gateway_status"
        echo ""

        # --- Agent Status ---
        echo -e "${BOLD}${WHITE}Agent Team Status${NC}"
        echo -e "${DIM}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        printf "  ${BOLD}%-22s %-8s %-12s %-15s${NC}\n" "Role" "Status" "Last Seen" "Session"

        for i in "${!ROLES[@]}"; do
            local role="${ROLES[$i]}"
            local icon="${ROLE_ICONS[$i]}"
            local status
            status=$(get_role_status "$role")

            local status_icon
            status_icon=$(print_status_icon "$status")
            
            local color="${NC}"
            case "$status" in
                active) color="${GREEN}" ;;
                idle) color="${BLUE}" ;;
                ready) color="${DIM}" ;;
                error) color="${RED}" ;;
                missing) color="${YELLOW}" ;;
            esac

            local last_seen="Never"
            local profile_dir="$PROFILES_DIR/$role"
            if [ -d "$profile_dir/sessions" ]; then
                local latest
                latest=$(ls -t "$profile_dir/sessions" 2>/dev/null | head -1)
                if [ -n "$latest" ]; then
                    last_seen=$(stat -c %y "$profile_dir/sessions/$latest" 2>/dev/null | cut -d'.' -f1 | cut -d' ' -f2 || echo "Unknown")
                fi
            fi

            local session_id
            session_id=$(ls -t "$profile_dir/sessions" 2>/dev/null | head -1 | cut -d_ -f1 || echo "-")
            session_id="${session_id:0:12}"

            printf "  ${icon} %-18s ${color}%-8s${NC} %-12s %-15s\n" "$role" "$status" "$last_seen" "$session_id"
        done
        echo ""

        # --- Kanban Summary ---
        echo -e "${BOLD}${WHITE}Kanban Board${NC}"
        echo -e "${DIM}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        local kb_data
        kb_data=$(get_kanban_summary)
        IFS='|' read -r total todo in_progress review done_count <<< "$kb_data"

        echo -e "  Total: ${WHITE}${BOLD}${total}${NC}   |   📋 TODO: ${YELLOW}${todo}${NC}   |   🔄 In Progress: ${CYAN}${in_progress}${NC}   |   👀 Review: ${MAGENTA}${review}${NC}   |   ✅ Done: ${GREEN}${done_count}${NC}"
        echo ""

        if [ "$total" -gt 0 ]; then
            echo -e "  ${BOLD}Progress:${NC} "
            local progress_pct=$(( done_count * 100 / (total + 1) ))
            print_bar "$progress_pct" 100 40
            echo -e " ${WHITE}${BOLD}${progress_pct}%${NC}"
        fi
        echo ""

        # --- Cost & Budget ---
        echo -e "${BOLD}${WHITE}Cost Tracking${NC}"
        echo -e "${DIM}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        local token_data
        token_data=$(get_token_usage)
        IFS='|' read -r input_tokens output_tokens <<< "$token_data"
        local cost_data
        cost_data=$(get_cost_estimate "$input_tokens" "$output_tokens")
        IFS='|' read -r cost_input cost_output total_cost <<< "$cost_data"

        echo -e "  Input Tokens:  ${WHITE}$(printf '%\x27d' "$input_tokens" 2>/dev/null || echo "$input_tokens")${NC}"
        echo -e "  Output Tokens: ${WHITE}$(printf '%\x27d' "$output_tokens" 2>/dev/null || echo "$output_tokens")${NC}"
        echo -e "  Est. Cost:     ${WHITE}\$$total_cost${NC}"

        if [ "$budget" != "0" ] && [ -n "$budget" ]; then
            local budget_pct=$(python3 -c "print(min(int(float('$total_cost') / float('$budget') * 100), 100))" 2>/dev/null || echo 0)
            echo -e "  Budget:        ${WHITE}\$${total_cost} / \$${budget}${NC}"
            
            if [ "$(echo "$total_cost >= $budget" | python3 -c "import sys; print(int(float(sys.stdin.read()) >= 0))" 2>/dev/null)" = "1" ]; then
                echo -e "  ${RED}${BOLD}⚠️  BUDGET EXCEEDED - Consider pausing agents${NC}"
            else
                printf "  ${BOLD}Budget Usage:${NC} "
                print_bar "$budget_pct" 100 20
                echo -e " ${WHITE}${BOLD}${budget_pct}%${NC}"
            fi
        fi
        echo ""

        # --- Footer ---
        echo -e "${DIM}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo -e "  ${DIM}Auto-refreshes every 3s | Press Ctrl+C to exit${NC}"
        echo -e "  ${DIM}Tip: Use 'hermes kanban list' for full task details${NC}"
        echo ""

        sleep 3
    done
}

# --- Cost Report Mode ---
run_cost_report() {
    echo -e "${BOLD}${WHITE}Rigor Cost Report${NC}"
    echo -e "${DIM}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""

    local token_data
    token_data=$(get_token_usage)
    IFS='|' read -r input_tokens output_tokens <<< "$token_data"
    local cost_data
    cost_data=$(get_cost_estimate "$input_tokens" "$output_tokens")
    IFS='|' read -r cost_input cost_output total_cost <<< "$cost_data"

    echo -e "  Input Tokens:  ${WHITE}$(printf '%\x27d' "$input_tokens" 2>/dev/null || echo "$input_tokens")${NC}"
    echo -e "  Output Tokens: ${WHITE}$(printf '%\x27d' "$output_tokens" 2>/dev/null || echo "$output_tokens")${NC}"
    echo -e "  Total Tokens:  ${WHITE}$(printf '%\x27d' $((input_tokens + output_tokens)) 2>/dev/null || echo "$((input_tokens + output_tokens))")${NC}"
    echo ""
    echo -e "  Cost Breakdown (Claude Sonnet 4 rates):"
    echo -e "    Input:   \$$cost_input  (\$3/MTok)"
    echo -e "    Output:  \$$cost_output (\$15/MTok)"
    echo -e "    ${BOLD}Total:   \$$total_cost${NC}"
    echo ""

    # Per-role breakdown if logs available
    echo -e "${BOLD}Per-Role Activity (Last 24h):${NC}"
    for i in "${!ROLES[@]}"; do
        local role="${ROLES[$i]}"
        local profile_dir="$PROFILES_DIR/$role"
        local session_count=0
        if [ -d "$profile_dir/sessions" ]; then
            session_count=$(ls "$profile_dir/sessions" 2>/dev/null | wc -l)
        fi
        local status
        status=$(get_role_status "$role")
        local icon
        icon=$(print_status_icon "$status")
        printf "  ${icon} %-20s %d sessions\n" "$role" "$session_count"
    done
}

# --- Budget Management ---
manage_budget() {
    local amount="$1"
    if [ -z "$amount" ]; then
        local current
        current=$(get_budget)
        if [ "$current" = "0" ] || [ -z "$current" ]; then
            echo -e "${YELLOW}No budget set. Use: $0 --budget <amount>${NC}"
        else
            echo -e "${GREEN}Current budget: \$$current${NC}"
        fi
        return
    fi

    set_budget "$amount"
    echo -e "${GREEN}Budget set to \$$amount${NC}"
    echo -e "${DIM}Rigor will warn when estimated cost exceeds this limit.${NC}"
}

# --- One-shot Status ---
run_status() {
    echo -e "${BOLD}${WHITE}Rigor System Status${NC}"
    echo -e "${DIM}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    
    # Hermes
    if command -v hermes &>/dev/null; then
        echo -e "  Hermes: ${GREEN}$(hermes --version 2>/dev/null | head -1)${NC}"
    else
        echo -e "  Hermes: ${RED}Not installed${NC}"
    fi

    # Model
    local model
    model=$(hermes config get model.default 2>/dev/null || echo "Not set")
    echo -e "  Model:  ${WHITE}${model}${NC}"

    # Profiles
    local active=0 idle=0 error=0
    for role in "${ROLES[@]}"; do
        case "$(get_role_status "$role")" in
            active) active=$((active+1)) ;;
            idle|ready) idle=$((idle+1)) ;;
            error|missing) error=$((error+1)) ;;
        esac
    done
    echo -e "  Agents: ${GREEN}${active} active${NC} | ${BLUE}${idle} idle${NC} | ${RED}${error} issues${NC}"

    # Kanban
    local kb_data
    kb_data=$(get_kanban_summary)
    IFS='|' read -r total todo in_progress review done_count <<< "$kb_data"
    echo -e "  Kanban: ${WHITE}${total} tasks${NC} (${YELLOW}${todo} todo${NC}, ${CYAN}${in_progress} running${NC}, ${GREEN}${done_count} done${NC})"

    # Cost
    local token_data
    token_data=$(get_token_usage)
    IFS='|' read -r input_tokens output_tokens <<< "$token_data"
    local cost_data
    cost_data=$(get_cost_estimate "$input_tokens" "$output_tokens")
    IFS='|' read -r _ _ total_cost <<< "$cost_data"
    echo -e "  Cost:   ${WHITE}\$$total_cost${NC} (est.)"
}

# --- Entry Point ---
case "${1:-}" in
    --cost)
        run_cost_report
        ;;
    --budget)
        manage_budget "${2:-}"
        ;;
    --status)
        run_status
        ;;
    *)
        run_dashboard
        ;;
esac
