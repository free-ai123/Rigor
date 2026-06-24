# OpenClaw -> Hermes Migration Report

- Timestamp: 20260513T204129
- Mode: execute
- Source: `/root/.openclaw`
- Target: `/root/.hermes/profiles/orchestrator`

## Summary

- migrated: 1
- archived: 3
- skipped: 36
- conflict: 2
- error: 0

## Warnings

- Conflicts were found. Re-run with --overwrite to replace conflicting targets after item-level backups.
- A config.yaml write hit a conflict or error mid-apply; later config items were skipped to avoid a partial write.

## What Was Not Fully Brought Over

- `/root/.openclaw/workspace/AGENTS.md` -> `(n/a)`: No workspace target was provided
- `(n/a)` -> `/root/.hermes/profiles/orchestrator/memories/MEMORY.md`: Source file not found
- `/root/.openclaw/openclaw.json` -> `/root/.hermes/profiles/orchestrator/.env`: No Hermes-compatible messaging settings found
- `/root/.openclaw/openclaw.json` -> `/root/.hermes/profiles/orchestrator/.env`: No allowlisted Hermes-compatible secrets found
- `/root/.openclaw/openclaw.json` -> `/root/.hermes/profiles/orchestrator/.env`: No Discord settings found
- `/root/.openclaw/openclaw.json` -> `/root/.hermes/profiles/orchestrator/.env`: No Slack settings found
- `/root/.openclaw/openclaw.json` -> `/root/.hermes/profiles/orchestrator/.env`: No WhatsApp settings found
- `/root/.openclaw/openclaw.json` -> `/root/.hermes/profiles/orchestrator/.env`: No Signal settings found
- `/root/.openclaw/openclaw.json` -> `/root/.hermes/profiles/orchestrator/.env`: No provider API keys found
- `(n/a)` -> `(n/a)`: blocked by earlier apply conflict
- `(n/a)` -> `(n/a)`: blocked by earlier apply conflict
- `(n/a)` -> `/root/.hermes/profiles/orchestrator/skills/openclaw-imports`: No OpenClaw skills directory found
- `(n/a)` -> `/root/.hermes/profiles/orchestrator/skills/openclaw-imports`: No shared OpenClaw skills directories found
- `(n/a)` -> `/root/.hermes/profiles/orchestrator/memories/MEMORY.md`: No workspace/memory/ directory found
- `(n/a)` -> `/root/.hermes/profiles/orchestrator/tts`: Source directory not found
- `/root/.openclaw/openclaw.json` -> `(n/a)`: Selected Hermes-compatible values were extracted; raw OpenClaw config was not copied.
- `/root/.openclaw/memory/main.sqlite` -> `(n/a)`: Contains secrets, binary state, or product-specific runtime data
- `/root/.openclaw/credentials` -> `(n/a)`: Contains secrets, binary state, or product-specific runtime data
- `/root/.openclaw/devices` -> `(n/a)`: Contains secrets, binary state, or product-specific runtime data
- `/root/.openclaw/identity` -> `(n/a)`: Contains secrets, binary state, or product-specific runtime data
- `(n/a)` -> `(n/a)`: blocked by earlier apply conflict
- `(n/a)` -> `(n/a)`: blocked by earlier apply conflict
- `(n/a)` -> `(n/a)`: blocked by earlier apply conflict
- `(n/a)` -> `(n/a)`: blocked by earlier apply conflict
- `(n/a)` -> `(n/a)`: blocked by earlier apply conflict
- `(n/a)` -> `(n/a)`: blocked by earlier apply conflict
- `(n/a)` -> `(n/a)`: blocked by earlier apply conflict
- `(n/a)` -> `(n/a)`: blocked by earlier apply conflict
- `(n/a)` -> `(n/a)`: blocked by earlier apply conflict
- `(n/a)` -> `(n/a)`: blocked by earlier apply conflict
- `(n/a)` -> `(n/a)`: blocked by earlier apply conflict
- `(n/a)` -> `(n/a)`: blocked by earlier apply conflict
- `(n/a)` -> `(n/a)`: blocked by earlier apply conflict
- `(n/a)` -> `(n/a)`: blocked by earlier apply conflict
- `(n/a)` -> `(n/a)`: blocked by earlier apply conflict
- `(n/a)` -> `(n/a)`: blocked by earlier apply conflict
- `/root/.openclaw/workspace/SOUL.md` -> `/root/.hermes/profiles/orchestrator/SOUL.md`: Target exists and overwrite is disabled
- `/root/.openclaw/openclaw.json` -> `/root/.hermes/profiles/orchestrator/config.yaml`: Model already set and overwrite is disabled

## Next Steps

- Review the migration report at /root/.hermes/profiles/orchestrator/migration/openclaw/20260513T204129/summary.md
- Start a new Hermes session (or /reset) to pick up the imported config.
- Re-run with --overwrite to apply items that were blocked by conflicts.
