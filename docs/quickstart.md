# Quick Start

## Prerequisites

1. **Python 3.10+**
2. **API Key** for the model provider you plan to use
3. **RAM**: 2GB minimum (5 roles), 4GB recommended (all 12 roles)

## 5 Minutes to Your First Project

### Step 1: Install Rigor

```bash
git clone https://github.com/free-ai123/Rigor.git
cd Rigor
bash scripts/bootstrap.sh
```

The script will:
- Create `.venv`
- Install Rigor runtime dependencies and security scanning helpers
- Install 12 role profiles to `~/.hermes/profiles/`
- Configure Kanban (auto-decompose, dispatch interval)
- Start Gateway processes for each role
- Run verification checks

For CLI-only installation without Hermes profile setup:

```bash
bash scripts/bootstrap.sh --skip-hermes
```

For contributor tooling and the deprecated custom TUI dependencies:

```bash
bash scripts/bootstrap.sh --dev
```

After bootstrap, either activate the virtualenv:

```bash
source .venv/bin/activate
rigor chat
```

Or run through the repository wrapper without activation:

```bash
./scripts/rigor.sh chat
```

`rigor chat` launches the Rigor `orchestrator` Hermes profile and automatically syncs the user's current Hermes login/provider/model into that profile first. The legacy `rigor tui` command is deprecated and forwards to this chat mode. Use `./scripts/rigor.sh chat --no-sync-profile` only when you explicitly want isolated profile-specific config.

### Step 2: Create Your First Task

For a fresh application scaffold, create it outside the Rigor checkout:

```bash
rigor init my-new-api
# Default output: ~/projects/my-new-api
```

Frame the problem before decomposition:

```bash
rigor frame "Build a URL shortener with custom codes and click tracking" --dir ~/projects/my-new-api --confirm
```

```bash
hermes kanban create "Build a URL shortener with custom codes and click tracking" --triage
```

Wait 60 seconds. The Orchestrator will automatically:
1. Read or create the Problem Frame and wait for user confirmation
2. Detect project type (Web Application)
3. Activate relevant roles (all 12)
4. Decompose into a DAG of 14+ tasks
5. Assign tasks to matching roles

### Step 3: Watch It Work

```bash
# View task list
hermes kanban list

# View task dependency tree
hermes kanban show 1 --tree

# View live project dashboard
cat ~/.hermes/kanban/workspace/shared/structured/project-dashboard.json | python3 -m json.tool

# View local code structure for agent context selection
./scripts/rigor.sh code-map --dir .
```

### Step 4: Check Results

When complete, find deliverables at:
- **Code**: `~/projects/<project-name>/`
- **Docs**: `~/projects/<project-name>/README.md`
- **Test Report**: `artifacts/qa-engineer/test-report.md`
- **Security Report**: `artifacts/security-auditor/`
- **Retrospective**: `shared/retrospectives/<project-name>-retro.md`

## Configuration

### Reduce Memory Usage

For small projects, stop unused roles to save RAM:

```bash
# Pure backend project: stop frontend + data roles
hermes gateway stop -p frontend-engineer
hermes gateway stop -p data-scientist
hermes gateway stop -p data-engineer

# Saves ~1GB RAM (runs on ~2GB total)
```

### Change Model

Edit `~/.hermes/profiles/*/config.yaml` to use a different model:

```yaml
model:
  default: qwen3.7-max  # Change to your preferred model
```

## Common Workflows

### New Feature Development
```
User → triage → PRD → Architecture → Backend + Frontend → Contract Gate → Review → Test/Smoke → Security → Deploy → UAT → Docs
```

### Bug Fix (Fast Track)
```
User → triage → Engineer Fix → Review → QA Verify
```

### Data Analysis
```
User → triage → PM Define → Data Scientist Analyze → PM Report
```

## Troubleshooting

### Gateway won't start
```bash
hermes gateway status
hermes -p <role> gateway run  # Run in foreground to see errors
```

### Webhook rejects requests
If `RIGOR_WEBHOOK_SECRET` is set, GitHub requests must send `X-Hub-Signature-256` and GitLab requests must send `X-Gitlab-Token`.

### Auto-decompose not triggering
```bash
hermes config show  # Check kanban.auto_decompose is true
hermes kanban decompose <task-id>         # Manual trigger
```

### Task stuck
```bash
hermes kanban reclaim <task-id>  # Re-assign to a fresh worker
```

### Out of memory
```bash
# Add 4GB swap
sudo fallocate -l 4G /swapfile && sudo chmod 600 /swapfile && sudo mkswap /swapfile && sudo swapon /swapfile
```

## Next Steps

- Read [Architecture](architecture.md) for how the system works
- Read [Troubleshooting](troubleshooting.md) for common issues
- Check the [Rigor README](../README.md) for full documentation
