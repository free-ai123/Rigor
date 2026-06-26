#!/usr/bin/env bash
# ============================================================
# Rigor CLI v1.0 - Unified Command Interface
#
# Usage:
#   rigor install              # Install Rigor expert team
#   rigor uninstall            # Uninstall expert team
#   rigor status               # System status snapshot
#   rigor monitor              # Real-time TUI dashboard
#   rigor cost                 # Cost report
#   rigor budget [amount]      # Set/view budget
#   rigor init <project-name>  # Scaffold new project
#   rigor kanban               # Quick kanban view
#   rigor help                 # Show help
# ============================================================
set -uo pipefail

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
REPO_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

# --- Colors ---
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

usage() {
    echo ""
    echo -e "${BOLD}${CYAN}Rigor CLI v1.0 - 12-Role AI Engineering Team${NC}"
    echo ""
    echo -e "  ${BOLD}Usage:${NC} rigor <command> [options]"
    echo ""
    echo -e "  ${BOLD}Commands:${NC}"
    echo "    install              Install Rigor expert team (Hermes profiles + Kanban)"
    echo "    uninstall            Remove expert team profiles"
    echo "    status               Quick system health snapshot"
    echo "    monitor              Real-time TUI dashboard (auto-refresh)"
    echo "    cost                 View token usage and cost estimate"
    echo "    budget [amount]      Set or view daily budget limit"
    echo "    init <project-name>  Scaffold a new project with Kanban board"
    echo "    kanban               Quick kanban task list"
    echo "    help                 Show this help message"
    echo ""
    echo -e "  ${BOLD}Examples:${NC}"
    echo "    rigor install                    # Deploy the team"
    echo "    rigor monitor                    # Watch live dashboard"
    echo "    rigor init my-url-shortener      # Start a new project"
    echo "    rigor kanban create 'Build API'  # Create a task"
    echo "    rigor budget 50                  # Set \$50 budget"
    echo ""
}

check_install() {
    if [ ! -f "$SCRIPT_DIR/setup-expert-team.sh" ]; then
        echo -e "${RED}Error: Rigor scripts not found. Please run from Rigor repository.${NC}"
        exit 1
    fi
}

case "${1:-help}" in
    install|i)
        check_install
        bash "$SCRIPT_DIR/setup-expert-team.sh"
        ;;
    uninstall|rm)
        check_install
        bash "$SCRIPT_DIR/setup-expert-team.sh" --uninstall
        ;;
    status|s)
        check_install
        bash "$SCRIPT_DIR/setup-expert-team.sh" --status
        echo ""
        bash "$SCRIPT_DIR/monitor.sh" --status
        ;;
    monitor|m)
        check_install
        bash "$SCRIPT_DIR/monitor.sh"
        ;;
    cost|c)
        check_install
        bash "$SCRIPT_DIR/monitor.sh" --cost
        ;;
    budget|b)
        check_install
        bash "$SCRIPT_DIR/monitor.sh" --budget "${2:-}"
        ;;
    init|new)
        check_install
        if [ -z "${2:-}" ]; then
            echo -e "${RED}Error: Project name required${NC}"
            echo "  Usage: rigor init <project-name>"
            exit 1
        fi
        bash "$SCRIPT_DIR/init-project.sh" "$2"
        ;;
    kanban|k)
        shift
        check_install
        hermes kanban "$@"
        ;;
    help|h|--help|-h|"")
        usage
        ;;
    *)
        echo -e "${RED}Unknown command: $1${NC}"
        echo ""
        usage
        exit 1
        ;;
esac
