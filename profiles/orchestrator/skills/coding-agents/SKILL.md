---
name: coding-agents
description: "Delegate coding tasks to autonomous AI coding agents: Claude Code, Codex CLI, or OpenCode CLI. Covers installation, one-shot tasks, interactive sessions, and parallel execution."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Coding-Agent, Claude, Codex, OpenCode, Autonomous, Code-Review, Refactoring, PTY]
---

# Coding Agents

Delegate coding tasks to autonomous AI coding agent CLIs. All three follow the same pattern: one-shot mode for bounded tasks, interactive PTY mode for multi-turn work.

## Choosing an Agent

| Agent | Install | Auth | One-shot | Interactive |
|-------|---------|------|----------|-------------|
| **Claude Code** | `npm i -g @anthropic-ai/claude-code` | OAuth or `ANTHROPIC_API_KEY` | `claude -p 'task'` | tmux + `claude` |
| **Codex** | `npm i -g @openai/codex` | OAuth or `OPENAI_API_KEY` | `codex exec 'task'` | PTY + `codex` |
| **OpenCode** | `npm i -g opencode-ai` | `opencode auth login` | `opencode run 'task'` | PTY + `opencode` |

**All require a git repository** (or `mktemp -d && git init` for scratch work).

---

## Section A: Claude Code

Install: `npm install -g @anthropic-ai/claude-code`
Auth: `claude auth login` or set `ANTHROPIC_API_KEY`

### One-Shot (Print Mode) — PREFERRED
```python
terminal(command="claude -p 'Add error handling to all API calls in src/' --allowedTools 'Read,Edit' --max-turns 10", workdir="/path/to/project", timeout=120)
```

Key flags: `--output-format json`, `--max-turns N`, `--max-budget-usd N`, `--model sonnet|opus|haiku`, `--effort low|medium|high`, `--bare` (skip plugins/hooks), `--fallback-model haiku`

### Interactive (tmux)
```python
terminal(command="tmux new-session -d -s claude-work -x 140 -y 40")
terminal(command="tmux send-keys -t claude-work 'cd /path/to/project && claude' Enter")
# Wait for startup, then send task
terminal(command="sleep 5 && tmux send-keys -t claude-work 'Refactor auth module' Enter")
# Monitor
terminal(command="sleep 15 && tmux capture-pane -t claude-work -p -S -50")
```

**Critical:** Handle trust dialog (`Enter`) and permissions dialog (`Down`, `Enter`).

### Structured Output
```python
terminal(command="claude -p 'List all functions in src/' --output-format json --json-schema '{...}'", workdir="/project", timeout=90)
```

### Session Management
- `claude -c` — continue most recent session in current directory
- `claude -r <id>` — resume specific session
- `claude --fork-session` — fork when resuming

### CLAUDE.md
Auto-loaded from project root. Use for persistent project context. Rules directory: `.claude/rules/*.md`

### Key Pitfalls
1. `--dangerously-skip-permissions` dialog defaults to "No, exit" — must send Down then Enter
2. Print mode (`-p`) skips all interactive dialogs — preferred for automation
3. `--max-turns` prevents runaway loops — always set it (5-10 for most tasks)
4. Interactive mode REQUIRES tmux — raw PTY alone isn't enough for orchestration
5. Context degrades above 70% window usage — use `/compact` proactively

---

## Section B: Codex CLI

Install: `npm install -g @openai/codex`
Auth: `OPENAI_API_KEY` or Codex OAuth (`~/.codex/auth.json`)

### One-Shot
```python
terminal(command="codex exec 'Add dark mode toggle to settings'", workdir="~/project", pty=True)
```

### Background (Long Tasks)
```python
terminal(command="codex exec --full-auto 'Refactor auth to use JWT'", workdir="~/project", background=True, pty=True, notify_on_complete=True)
# Monitor: process(action="poll"/"log"/"wait", session_id="...")
# Send input: process(action="submit", session_id="...", data="yes")
```

### Key Flags
| Flag | Effect |
|------|--------|
| `exec "prompt"` | One-shot execution, exits when done |
| `--full-auto` | Sandboxed, auto-approves file changes |
| `--yolo` | No sandbox, no approvals (fastest, most dangerous) |

### Parallel Issue Fixing with Worktrees
```python
terminal(command="git worktree add -b fix/issue-78 /tmp/issue-78 main", workdir="~/project")
terminal(command="codex --yolo exec 'Fix issue #78. Commit when done.'", workdir="/tmp/issue-78", background=True, pty=True)
```

### Key Pitfalls
1. **Always use `pty=True`** — Codex is interactive and hangs without PTY
2. **Git repo required** — use `mktemp -d && git init` for scratch
3. **`--full-auto` for building** — auto-approves changes within sandbox
4. **Don't interfere** — monitor with `poll`/`log`, be patient

---

## Section C: OpenCode CLI

Install: `npm i -g opencode-ai@latest` or `brew install anomalyco/tap/opencode`
Auth: `opencode auth login` or set provider env vars

### One-Shot
```python
terminal(command="opencode run 'Add retry logic to API calls'", workdir="~/project")
```

Attach files: `opencode run 'Review this' -f config.yaml -f .env.example`

### Interactive (Background)
```python
terminal(command="opencode", workdir="~/project", background=True, pty=True)
process(action="submit", session_id="<id>", data="Implement OAuth refresh flow")
process(action="poll"/"log", session_id="<id>")
# Exit: process(action="write", session_id="<id>", data="\x03")  # Ctrl+C
```

**CRITICAL:** Do NOT use `/exit` — it opens an agent selector. Use Ctrl+C (`\x03`) or `process(action="kill")`.

### Key Flags
| Flag | Use |
|------|-----|
| `run 'prompt'` | One-shot, exits |
| `--continue` / `-c` | Continue last session |
| `--session <id>` | Continue specific session |
| `--model provider/model` | Force specific model |
| `--file <path>` / `-f` | Attach files |
| `--thinking` | Show model thinking blocks |

### Key Pitfalls
1. `opencode run` does NOT need pty — only interactive TUI mode does
2. `/exit` is NOT valid — use Ctrl+C
3. PATH mismatch can select wrong binary/model config
4. Don't share one working directory across parallel sessions

---

## Section D: Parallel Execution Pattern

All three agents support parallel execution via separate tmux sessions or worktrees:

```python
# Pattern: start multiple agents in parallel
for name, task in [("backend", "Fix auth bug"), ("frontend", "Add login form")]:
    terminal(command=f"tmux new-session -d -s {name} -x 140 -y 40", timeout=10)
    terminal(command=f"tmux send-keys -t {name} 'cd ~/project && claude -p \"{task}\" --max-turns 10' Enter", timeout=5)

# Monitor all
terminal(command="for s in backend frontend; do echo '=== '$s' ==='; tmux capture-pane -t $s -p -S -5; done")
```

## General Rules

1. **Prefer one-shot mode** for single tasks — cleaner, no dialog handling
2. **Always set resource limits** (`--max-turns`, `--max-budget-usd`)
3. **Scope to a single repo/workdir** — never share working directories
4. **Monitor before killing** — check progress logs before terminating
5. **Report concrete outcomes** — files changed, tests passed, remaining risks
6. **Clean up** — kill tmux sessions, remove worktrees when done
