# Quick Start

## Prerequisites

1. **Hermes Agent** installed: `curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash`
2. **API Key** configured in `~/.hermes/.env`
3. **RAM**: 2GB minimum (5 roles), 4GB recommended (all 12 roles)

## 5 Minutes to Your First Project

### Step 1: Install Rigor

```bash
git clone https://github.com/rigor-dev/rigor.git
cd rigor
bash scripts/setup-expert-team.sh
```

The script will:
- Install 12 role profiles to `~/.hermes/profiles/`
- Configure Kanban (auto-decompose, dispatch interval)
- Start Gateway processes for each role
- Run verification checks

### Step 2: Create Your First Task

```bash
hermes kanban create "Build a URL shortener with custom codes and click tracking" --triage
```

Wait 60 seconds. The Orchestrator will automatically:
1. Detect project type (Web Application)
2. Activate relevant roles (all 12)
3. Decompose into a DAG of 14+ tasks
4. Assign tasks to matching roles

### Step 3: Watch It Work

```bash
# View task list
hermes kanban list

# View task dependency tree
hermes kanban show 1 --tree

# View live project dashboard
cat ~/.hermes/kanban/workspace/shared/structured/project-dashboard.json | python3 -m json.tool
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
User → triage → PRD → Architecture → Backend + Frontend → Review → Test → Security → Deploy → UAT → Docs
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

### Auto-decompose not triggering
```bash
hermes config get kanban.auto_decompose  # Should be "true"
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
