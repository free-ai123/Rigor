# Maintenance Guide

This guide keeps Rigor reproducible for maintainers and contributors.

## Local Checks

Run the full local gate before opening a pull request:

```bash
bash scripts/bootstrap.sh --skip-hermes --full-check
```

Useful focused commands:

```bash
make check
make scan
./scripts/rigor.sh code-map --dir .
```

The default test command enforces branch coverage with a conservative 40% baseline threshold. Raise the threshold as newly covered integration paths land.

## CI Expectations

CI runs on Python 3.10 through 3.13. The project intentionally requires Python 3.10+ because the source uses modern typing syntax such as `dict[str, Any]` and `str | None`.

The Docker job builds `.devcontainer/Dockerfile`, which installs the editable package with dev dependencies.

## Webhook Security

Do not expose `rigor webhook` without a secret:

```bash
export RIGOR_WEBHOOK_SECRET="replace-with-a-long-random-token"
rigor webhook --port 9999
```

GitHub requests must include `X-Hub-Signature-256`; GitLab requests must include `X-Gitlab-Token`.

## Agent Terminal Safety

`AgentTerminal` deliberately blocks shell commands, inline Python execution, destructive Git commands, and delete-style `find` operations. Prefer adding narrow, reviewed command templates over expanding the global allowlist.

## Release Checklist

1. Update `CHANGELOG.md`.
2. Run `make check`.
3. Verify `rigor --help`, `rigor status`, and `rigor code-map --dir .`.
4. Build the development image:

```bash
docker build -f .devcontainer/Dockerfile . -t rigor:release-check
```

5. Tag and publish according to the package registry process.
