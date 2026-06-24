# Terminal Block — Pitfall Reference

## Problem

Worker profiles' terminal commands are intercepted by a security scanner that requires manual approval. When the scanner denies commands (or the orchestrator lacks terminal tool access entirely), workers enter infinite retry loops:
1. Read existing files
2. Try to run a terminal command (`npm install`, `mysql`, `ls`)
3. Terminal denied/blocked
4. Re-plan: "I have enough context, let me write files directly"
5. Prepare write_file... but often get stuck before completing

## Detection Signs

- Task stays `running` for 10+ minutes
- `hermes kanban log <task_id>` shows repeated patterns:
  - `preparing terminal…` → `[error]` or `BLOCKED: User denied`
  - Or repeated `preparing execute_code…` loops without file writes
- No new files appear in the workspace

## Recovery Actions (in order of preference)

1. **Unblock**: `hermes kanban unblock <task_id>` — lets the worker try once more
2. **Check workspace**: `find /root/.hermes/kanban/workspaces/<task_id>/ -type f` — see if partial output exists
3. **Manual complete**: `hermes kanban complete <task_id> --summary "..."` — complete based on what was already done
4. **Write files directly**: If files weren't written, create them yourself in the persistent project directory
5. **Copy existing files**: `cp -r /root/.hermes/kanban/workspaces/<task_id>/collector-service/* /root/projects/<project>/collector-service/`

## Prevention

- Write detailed task descriptions so workers can complete with file writes alone
- Include explicit instructions: "Use write_file for all code changes. Do not use terminal for npm install or database queries."
- Start gateway processes before creating tasks: `hermes -p <profile> gateway run &`
- Pre-install dependencies in the persistent project directory: `cd /root/projects/<project>/collector-service && npm install`
- Pre-create `.env` files so workers don't need to create them
