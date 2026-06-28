#!/usr/bin/env bash
# ============================================================
# Rigor Project Scaffolding v1.0
#
# Usage:
#   ./scripts/init-project.sh <project-name>
#   ./scripts/init-project.sh my-url-shortener
#   ./scripts/init-project.sh "我的项目" --dir ~/projects/我的项目
# ============================================================
set -uo pipefail

# --- Colors ---
RED=$'\033[0;31m'
GREEN=$'\033[0;32m'
YELLOW=$'\033[1;33m'
BLUE=$'\033[0;34m'
CYAN=$'\033[0;36m'
BOLD=$'\033[1m'
NC=$'\033[0m'

log_info()    { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[OK]${NC}   $1"; }
log_warn()    { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error()   { echo -e "${RED}[ERROR]${NC} $1"; }

# --- Helpers ---
expand_path() {
    case "$1" in
        "~") printf "%s" "$HOME" ;;
        "~/"*) printf "%s/%s" "$HOME" "${1#~/}" ;;
        *) printf "%s" "$1" ;;
    esac
}

absolute_path() {
    local path="$1"
    case "$path" in
        /*) printf "%s" "$path" ;;
        *) printf "%s/%s" "$(pwd)" "$path" ;;
    esac
}

usage() {
    if [ "${1:-}" = "error" ]; then
        echo -e "${RED}Error: Project name required${NC}"
    fi
    echo "  Usage: init-project.sh <project-name> [--dir <target-dir>] [--base-dir <projects-dir>]"
    echo "  Default target: ~/projects/<project-name>"
}

# --- Input ---
if [ "${1:-}" = "-h" ] || [ "${1:-}" = "--help" ]; then
    usage
    exit 0
fi

PROJECT_NAME="${1:-}"
if [ -z "$PROJECT_NAME" ]; then
    usage error
    exit 1
fi
shift || true

TARGET_DIR=""
PROJECTS_ROOT="${RIGOR_PROJECTS_DIR:-$HOME/projects}"
while [ "$#" -gt 0 ]; do
    case "$1" in
        --dir)
            if [ -z "${2:-}" ]; then
                log_error "--dir requires a value"
                exit 1
            fi
            TARGET_DIR="$2"
            shift 2
            ;;
        --base-dir|--projects-dir)
            if [ -z "${2:-}" ]; then
                log_error "$1 requires a value"
                exit 1
            fi
            PROJECTS_ROOT="$2"
            shift 2
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            usage
            exit 1
            ;;
    esac
done

# Convert to a filesystem-safe directory name while preserving Chinese names.
PROJECT_SLUG=$(printf "%s" "$PROJECT_NAME" \
    | tr '[:upper:]' '[:lower:]' \
    | sed -E 's#[/\\:]+#-#g; s/[[:space:]]+/-/g; s/^-+//; s/-+$//')
if [ -z "$PROJECT_SLUG" ]; then
    PROJECT_SLUG="project-$(date +%Y%m%d%H%M%S)"
fi

if [ -n "$TARGET_DIR" ]; then
    WORKSPACE_DIR="$(absolute_path "$(expand_path "$TARGET_DIR")")"
else
    PROJECTS_ROOT="$(absolute_path "$(expand_path "$PROJECTS_ROOT")")"
    WORKSPACE_DIR="$PROJECTS_ROOT/$PROJECT_SLUG"
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
RIGOR_ROOT="$(cd "$SCRIPT_DIR/.." >/dev/null 2>&1 && pwd)"

# --- Welcome ---
echo ""
echo -e "${CYAN}${BOLD}╔══════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}${BOLD}║     🚀  Rigor Project Scaffolding            ║${NC}"
echo -e "${CYAN}${BOLD}╚══════════════════════════════════════════════╝${NC}"
echo ""
echo "  Project: ${BOLD}$PROJECT_NAME${NC} ($PROJECT_SLUG)"
echo "  Workspace: ${BOLD}$WORKSPACE_DIR${NC}"
echo ""

case "$WORKSPACE_DIR" in
    "$RIGOR_ROOT"|"$RIGOR_ROOT"/*)
        log_warn "Target is inside the Rigor repository. Prefer the default ~/projects/<project-name> layout."
        ;;
esac

# --- Create Workspace ---
log_info "Creating project workspace..."
mkdir -p "$(dirname "$WORKSPACE_DIR")"
mkdir -p "$WORKSPACE_DIR"/{kanban,reports,src,tests}
mkdir -p "$WORKSPACE_DIR/artifacts"/{orchestrator,product-manager,tech-lead,backend-engineer,frontend-engineer,qa-engineer}

# 1. Problem Framing Template
log_info "Creating Problem Framing template..."
cat > "$WORKSPACE_DIR/artifacts/orchestrator/problem-frame.md" << EOF
# Problem Frame: $PROJECT_NAME

## Original Request
[Paste the user's original request here]

## What
[What exact deliverable should be produced?]

## Why
[What decision, outcome, or user value should this work support?]

## Who
[Who is the primary audience or user?]

## How
[What format, interface, or artifact should be delivered?]

## Scope
- [In-scope item]

## Non-Goals
- [Explicitly out-of-scope item]

## Constraints
- [Time, budget, technology, compliance, platform, or operational limits]

## Success Criteria
- [Observable result that proves the work is good enough]

## Assumptions
- [Assumption made to keep progress moving]

## Unknowns
- [Question that must be clarified before implementation if high risk]

## User Confirmation
- Status: pending
- Confirmed By User: false
- Notes:
EOF

cat > "$WORKSPACE_DIR/artifacts/orchestrator/problem-frame.json" << EOF
{
  "original_request": "",
  "intent": "",
  "business_goal": "",
  "target_user": "",
  "deliverable": "",
  "scope": [],
  "non_goals": [],
  "constraints": [],
  "success_criteria": [],
  "assumptions": [],
  "unknowns": [],
  "clarification_questions": [],
  "mode": "draft",
  "confidence": 0.0,
  "should_block_execution": true,
  "confirmed_by_user": false,
  "confirmation_status": "pending",
  "confirmation_note": ""
}
EOF
log_success "Problem framing template created"

# 2. Project PRD Template (SDD Format)
log_info "Creating Product Requirements Document..."
cat > "$WORKSPACE_DIR/artifacts/product-manager/prd.md" << EOF
# Project: $PROJECT_NAME

## Problem Frame Source
- Markdown: artifacts/orchestrator/problem-frame.md
- JSON: artifacts/orchestrator/problem-frame.json

## Overview
[Describe the project goal in 1-2 sentences]

## User Stories

### Story 1: [Feature Name]
**As a** [user role]
**I want** [action]
**So that** [value]

#### Acceptance Criteria
**AC-1:**
- Given [precondition]
- When [user action]
- Then [expected result]

**AC-2:**
- Given [precondition]
- When [user action]
- Then [expected result]

### Story 2: [Feature Name]
**As a** [user role]
**I want** [action]
**So that** [value]

#### Acceptance Criteria
**AC-1:**
- Given [precondition]
- When [user action]
- Then [expected result]

## Technical Constraints
- [Constraint 1]
- [Constraint 2]

## Success Criteria
- [Criterion 1]
- [Criterion 2]
EOF
log_success "PRD template created"

# 3. Architecture Template
cat > "$WORKSPACE_DIR/artifacts/tech-lead/architecture.md" << EOF
# Architecture: $PROJECT_NAME

## System Design
[Describe system architecture]

## Tech Stack
- [Technology 1]
- [Technology 2]

## API Design
[API endpoints and contracts]

## Database Schema
[Tables and relationships]
EOF
log_success "Architecture template created"

# 4. Kanban Board Init
log_info "Initializing Kanban board for project..."

# Create a Kanban task template
cat > "$WORKSPACE_DIR/kanban/init-tasks.yaml" << EOF
# Initial Kanban tasks for: $PROJECT_NAME
# Load with: hermes kanban create --from-file init-tasks.yaml

tasks:
  - title: "Define project requirements and success criteria"
    description: "Product Manager: Write PRD based on artifacts/orchestrator/problem-frame.json and user needs"
    assignee: product-manager
    priority: high

  - title: "Design system architecture"
    description: "Tech Lead: Create architecture doc with tech stack selection"
    assignee: tech-lead
    priority: high
    depends_on: [1]

  - title: "Set up project repository and CI/CD"
    description: "DevOps Engineer: Initialize repo, configure CI pipeline"
    assignee: devops-engineer
    priority: high
    depends_on: [1]

  - title: "Implement core API endpoints"
    description: "Backend Engineer: Build REST API according to architecture"
    assignee: backend-engineer
    priority: medium
    depends_on: [2]

  - title: "Write unit and integration tests"
    description: "QA Engineer: TDD-first approach, coverage > 80%"
    assignee: qa-engineer
    priority: medium
    depends_on: [4]

  - title: "Security audit"
    description: "Security Auditor: Review code for vulnerabilities"
    assignee: security-auditor
    priority: high
    depends_on: [4]
EOF
log_success "Kanban task template created"

# 5. README Template
cat > "$WORKSPACE_DIR/README.md" << EOF
# $PROJECT_NAME

> Generated by Rigor AI Engineering Team

## Quick Start
\`\`\`bash
rigor monitor          # Watch team progress
rigor kanban list      # View task status
rigor cost             # Check budget usage
\`\`\`

## Project Structure
\`\`\`
$WORKSPACE_DIR/
├── artifacts/          # Design docs, PRD, architecture
│   ├── orchestrator/   # Problem frame and coordination artifacts
│   ├── product-manager/# PRD and user stories
│   └── tech-lead/      # Architecture and DAG plan
├── kanban/             # Task definitions and templates
├── reports/            # QA reports, security audits
├── src/                # Source code
└── tests/              # Test files
\`\`\`
EOF
log_success "README template created"

# 6. Project Profile for Hermes (Kanban workspace)
log_info "Configuring Hermes kanban workspace..."
mkdir -p "$WORKSPACE_DIR/.hermes"
cat > "$WORKSPACE_DIR/.hermes/config.yaml" << EOF
# Rigor project config for: $PROJECT_NAME
project:
  name: "$PROJECT_NAME"
  slug: "$PROJECT_SLUG"
  kanban_board: "$WORKSPACE_DIR/kanban/board.db"
  budget_daily: 0  # Set daily budget limit (0 = unlimited)

roles:
  - orchestrator
  - product-manager
  - tech-lead
  - backend-engineer
  - frontend-engineer
  - qa-engineer
  - security-auditor
  - devops-engineer
  - technical-writer
EOF
log_success "Project config created"

# 7. .gitignore
cat > "$WORKSPACE_DIR/.gitignore" << EOF
# Rigor workspace
*.db
.pytest_cache/
__pycache__/
node_modules/
.env
*.log
EOF
log_success ".gitignore created"

# --- Summary ---
echo ""
echo -e "${GREEN}${BOLD}============================================================${NC}"
echo -e "${GREEN}${BOLD}  🎉  Project '$PROJECT_NAME' scaffolded successfully!${NC}"
echo -e "${GREEN}${BOLD}============================================================${NC}"
echo ""
echo "  📁 Workspace: $WORKSPACE_DIR/"
echo ""
echo "  Next steps:"
echo "    1. Frame and confirm the problem: ${BOLD}rigor frame \"<request>\" --dir $WORKSPACE_DIR --confirm${NC}"
echo "    2. Edit ${BOLD}$WORKSPACE_DIR/artifacts/product-manager/prd.md${NC}"
echo "    3. Load tasks: ${BOLD}hermes kanban create --from-file $WORKSPACE_DIR/kanban/init-tasks.yaml${NC}"
echo "    4. Watch team: ${BOLD}rigor monitor${NC}"
echo ""
