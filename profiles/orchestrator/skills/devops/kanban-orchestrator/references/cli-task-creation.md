# CLI Task Creation Guide (for Orchestrators)

The orchestrator uses `hermes kanban create` CLI — NOT the Python `kanban_create()` tool (which is worker-only).

## Gateway Prerequisite

The dispatcher lives inside the gateway. **No gateway = no dispatch.**

```bash
# Check status
hermes gateway status

# Quick start (CLI sessions)
hermes gateway run &
sleep 3

# Or systemd (if installed)
hermes gateway start
```

Verify dispatch is working: after creating a task, `hermes kanban list` should show it transitioning from `ready` → `running` within ~60s (default tick interval).

## Task Creation

```bash
# Independent task
hermes kanban create "Short task title and description" --assignee <profile>

# With single parent
hermes kanban create "Title" --assignee <profile> --parent <task_id>

# With multiple parents (repeat --parent flag)
hermes kanban create "Title" --assignee <profile> --parent <id1> --parent <id2> --parent <id3>
```

## CLI Quirks & Workarounds

| Issue | Symptom | Fix |
|-------|---------|-----|
| **Multi-line bodies** | Shell interprets `$`, backticks in double-quoted strings | Use single quotes, or escape special chars |
| **Silent creation** | Empty output + exit code -1, but task IS created | Always verify with `hermes kanban list` |
| **Foreground warning** | "Foreground command uses '&'" error | Use `terminal(background=true)` for long commands |
| **Too many args** | Very long `--parent` chains cause truncation | Create in phases — parents first, then children |
| **Gateway not running** | Task sits in `ready` forever | `hermes gateway run &` first |

## Verification Loop

```bash
# After creating tasks, verify
hermes kanban list           # all tasks with status
hermes kanban show <task_id> # full details of one task
hermes kanban stats          # aggregate counts by status/assignee
```

## Progressive Creation Pattern

Don't create the entire graph upfront if intermediate outputs matter:

```
Phase 1: Create T0 (PRD) → wait for completion → read PRD output
Phase 2: Create T1 (arch review) + T2 (security) → wait → read reviews
Phase 3: Create T3 (DB design) + T4 (UI) → wait → read designs
Phase 4: Create T5 (API impl) + T6 (frontend impl) → wait
Phase 5: Create T7-T12 (review → test/security/deploy → UAT)
```

This lets the orchestrator adjust later task descriptions based on what earlier stages actually produced.

## Task Body Writing Tips

- **First line = clear role directive**: "你是 backend-engineer。..." — triggers the right context
- **Include dependency context**: "基于 T0 (PRD) 和 T1, T2 的审查意见..." — helps worker orient
- **Specify metadata expectations**: "完成后 metadata 必须包含: api_endpoints, db_migrations" — ensures structured handoff
- **Keep under 500 chars** if possible — very long bodies are harder for workers to parse at startup
