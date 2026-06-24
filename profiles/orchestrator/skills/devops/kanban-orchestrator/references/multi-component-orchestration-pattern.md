# Multi-Component Orchestration — Session Pattern & Recovery

## Standard timing expectations (polled every 60-180s)
| Task type | Expected duration | Block risk |
|-----------|------------------|------------|
| PRD (product-manager) | 3-5 min | Low |
| Architecture/security review | 3-5 min | Low |
| DB + API design (backend) | 5-8 min | Medium (terminal verify) |
| Rust skeleton (backend) | 5-8 min | Medium (cargo check blocked) |
| UI prototype (frontend) | 5-10 min | High (npm install blocked, GC) |
| Full implementation (Python) | 10-20 min | Medium (delegate_task subagents) |
| Full implementation (Rust) | 5-10 min | Medium (cargo build blocked) |
| Full implementation (Next.js) | 10-20 min | High (GC cycles, npm install) |
| Docker/infra (devops) | 5-8 min | Medium |
| Code review (code-reviewer) | 5-10 min | Low |
| Testing (qa-engineer) | 5-10 min | Medium |
| Security audit (security-auditor) | 5-8 min | Low |
| Deploy prep (devops) | 5-8 min | Medium |
| Deployment (devops) | 5-10 min | High (docker not available) |
| UAT (product-manager) | 3-5 min | Low |
| Fix task (any) | 5-10 min | Medium |

## Recovery decision tree
```
Task blocked?
  ├─ Terminal command blocked? → unblock + wait 60s
  ├─ Still blocked after unblock? → check if files exist
  │   ├─ Files exist (find ... | wc -l > 10) → manual complete
  │   └─ No files → unblock + wait 120s + check again
  ├─ Worker says "workspace empty"? → it's rebuilding via batch write
  │   ├─ Check log for "from hermes_tools import write_file"
  │   ├─ If present → wait 3-5 min, likely succeeds
  │   └─ If absent → unblock + wait
  └─ Loop > 3 unblock cycles? → manual complete + note known issues
```

## UAT rejection handling
```
UAT rejected → create fix task (assignee=original author, parents=[UAT])
  ├─ Fix completes → create Re-UAT (parents=[fix])
  │   ├─ Re-UAT passes → archive
  │   └─ Re-UAT rejects:
  │       ├─ Reason: "code lost to scratch GC" → check /root/projects/
  │       │   ├─ Fix exists in persistent dir → archive with known issues
  │       │   └─ Fix missing → create new fix task
  │       └─ Reason: actual bugs → create another fix task
  └─ Fix task blocked → apply recovery decision tree above
```

## Key commands reference
```bash
# Start missing gateways
hermes gateway run --profile <name> &

# Check all tasks
hermes kanban list

# Check specific task
hermes kanban list 2>&1 | grep <task_id>
hermes kanban show <task_id>
hermes kanban log <task_id> 2>&1 | tail -20

# Unblock stuck task
hermes kanban unblock <task_id>

# Manually complete (when files exist but worker is stuck)
hermes kanban complete <task_id> --summary "Brief description of what was produced"

# Create task with multiple parents
hermes kanban create 'task body' --assignee <profile> --parent <id1> --parent <id2>

# Verify files exist
find /root/projects/<project>/<component> -type f | wc -l
```

## Common block triggers
| Command | Blocks? | Workaround |
|---------|---------|------------|
| `npm install` | Yes | Defer to next worker or manual complete |
| `cargo check` | No (but fails without Rust) | Check file count, defer to T7 |
| `docker compose up` | No (but fails without Docker) | Verify docker-compose.yml, defer to production |
| `alembic upgrade` | Yes (needs DB connection) | Skip in orchestrator env |
| `python -m py_compile` | Sometimes | Use `find ... | wc -l` instead |
| `git init/commit` | No | Safe to run |
