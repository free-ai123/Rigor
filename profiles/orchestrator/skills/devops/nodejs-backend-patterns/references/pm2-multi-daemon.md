# PM2 Multi-Daemon Management in Hermes Environments

## The Problem

When working with Express services in a Hermes Agent environment, you may encounter services that "come back to life" after being killed. This is because **each Hermes profile maintains its own PM2 daemon**.

## Profile-level PM2 Daemons

```
/root/.pm2                              # Default PM2 (system-level)
/root/.hermes/profiles/devops-engineer/home/.pm2   # devops-engineer PM2
/root/.hermes/profiles/orchestrator/home/.pm2      # orchestrator PM2
# ... one per profile
```

Each daemon is independent. A service started by `devops-engineer`'s PM2 will NOT appear in `pm2 list` run from the default profile.

## Detection

```bash
# Find all PM2 God Daemons
ps aux | grep 'God Daemon'

# Find which port is being used
ss -tlnp sport = :8000
# Output: users:(("node /root/.her...",pid=570714,fd=23))

# Check the process's parent
ps -o pid,ppid,cmd -p 570714
# PPID points to a God Daemon
```

## Stopping a Service

### Method 1: Via the correct PM2

```bash
PM2_HOME=/root/.hermes/profiles/devops-engineer/home/.pm2 pm2 list
PM2_HOME=/root/.hermes/profiles/devops-engineer/home/.pm2 pm2 stop report-center
PM2_HOME=/root/.hermes/profiles/devops-engineer/home/.pm2 pm2 delete report-center
```

### Method 2: Kill the daemon directly

```bash
ps aux | grep 'God Daemon.*devops-engineer'
kill <daemon-pid>
```

### Method 3: Nuclear option (all node processes)

```bash
pkill -9 -f node
pgrep -af node  # verify
```

## Prevention

When a Kanban task deploys a service via PM2, always note which profile's PM2 was used. Before starting a new test instance:

1. Check if the port is in use: `ss -tlnp sport = :8000`
2. If occupied, find and stop the owning PM2
3. Only then start the new instance
