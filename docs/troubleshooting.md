# Troubleshooting

## Common Issues

### Gateway won't start

```bash
# Check status
hermes gateway status

# Run in foreground to see errors
hermes -p <role> gateway run
```

Common causes:
- **Port conflict**: Another Gateway is already using the port
- **Config error**: Invalid YAML in `config.yaml`
- **Model unavailable**: The configured model/provider isn't accessible

### Auto-decompose not triggering

```bash
# Check config
hermes config show  # Check kanban.auto_decompose and kanban.dispatch_in_gateway are true

# Manual trigger
hermes kanban decompose <task-id>
```

### Task stuck in "triage"

1. Check if orchestrator Gateway is running: `hermes gateway status -p orchestrator`
2. Check if auxiliary LLM is configured with `hermes config show`.
3. Manually trigger: `hermes kanban decompose <task-id>`

### Task stuck in "running"

```bash
# Check if worker Gateway is alive
hermes gateway status -p <role>

# If dead, reclaim and reassign
hermes kanban reclaim <task-id>
```

### Out of memory

```bash
# Check available memory
free -h

# Stop unused roles to save RAM
hermes gateway stop -p data-scientist
hermes gateway stop -p data-engineer

# Add swap if needed (4GB)
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

### Quality gate fails repeatedly

If a task fails the quality gate 3 times:
1. Check the escalation report in the project dashboard
2. Review the root cause analysis
3. Either fix the underlying issue or adjust the quality threshold

### Knowledge not being injected

1. Check that `knowledge-index.json` has entries for your project type
2. Verify the project type matches an injection rule in `project-profiles.json`
3. Check that entries have `status: "active"` (not `stale` or `archived`)

### Setup script fails

```bash
# Run with debug output
bash -x scripts/setup-expert-team.sh

# Check Hermes is installed
hermes --version

# Check API key is configured
cat ~/.hermes/.env
```

## Getting Help

- **Issues**: [GitHub Issues](https://github.com/free-ai123/Rigor/issues)
- **Discussions**: [GitHub Discussions](https://github.com/free-ai123/Rigor/discussions)
- **Hermes docs**: https://hermes-agent.nousresearch.com/docs/
