# Security Policy

## Supported Versions

Rigor is currently pre-1.0 operational software published as `2.0.0` for the CLI package line. Security fixes target the current `main` branch.

## Reporting a Vulnerability

Please do not open a public issue for a suspected vulnerability. Send a private report to the repository maintainers with:

- Affected command, module, or workflow.
- Reproduction steps and expected impact.
- Any relevant payloads, logs, or sample webhook headers.

## Operational Guidance

- Set `RIGOR_WEBHOOK_SECRET` before exposing `rigor webhook` outside localhost.
- Run agent command execution in a disposable workspace.
- Avoid mounting sensitive home directories into development containers unless required.
- Review generated patches before committing them.
