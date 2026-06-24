# Collector Service Monitoring Reference

> Absorbed from `nodejs-collector-pattern`. ETH/BSC/TRON multi-chain collector service monitoring queries.

## Quick Status Check

```bash
cd /root/projects/collector-service/collector-service
node scripts/check_status.js
```

## Full End-to-End Test

```bash
node scripts/test_all.js
```

## Key MySQL Queries

### Health Dashboard (One Query)
```sql
SELECT
  (SELECT COUNT(*) FROM system_alert WHERE status=0 AND level='CRITICAL') as critical_alerts,
  (SELECT COUNT(*) FROM system_alert WHERE status=0 AND level='ERROR') as error_alerts,
  (SELECT COUNT(*) FROM chain_transaction WHERE status=1) as pending_txs,
  (SELECT COUNT(*) FROM collect_task WHERE status=7 AND updated_at > UNIX_TIMESTAMP()-3600) as failed_1h,
  (SELECT COUNT(*) FROM collect_task WHERE status IN (0,3) AND created_at < UNIX_TIMESTAMP()-300) as stuck_tasks;
```

### Interpretation
| Metric | OK | Warning | Critical |
|--------|-----|---------|----------|
| critical_alerts | 0 | > 0 | > 0 (investigate immediately) |
| error_alerts | < 5 | 5-10 | > 10 |
| pending_txs | < 20 | 20-50 | > 50 |
| failed_1h | < 5 | 5-20 | > 20 |
| stuck_tasks | < 50 | 50-100 | > 100 |

### Task Distribution
```sql
SELECT chain, symbol, status, COUNT(*) as cnt
FROM collect_task GROUP BY chain, symbol, status ORDER BY chain, symbol, status;
```

### Pending Transactions
```sql
SELECT chain, tx_hash, tx_type, amount,
  expire_at - UNIX_TIMESTAMP() as seconds_left,
  FROM_UNIXTIME(expire_at) as expires_at
FROM chain_transaction WHERE status=1 ORDER BY expire_at ASC;
```

### Failed Transactions (Last 24h)
```sql
SELECT chain, symbol, tx_hash, error_msg,
  FROM_UNIXTIME(updated_at) as failed_at
FROM chain_transaction WHERE status=3 AND updated_at > UNIX_TIMESTAMP()-86400
ORDER BY updated_at DESC;
```

### RPC Node Status
```sql
SELECT chain, url, priority, status, fail_count,
  FROM_UNIXTIME(last_success_at) as last_ok,
  FROM_UNIXTIME(last_fail_at) as last_err
FROM rpc_endpoint ORDER BY chain, priority;
```

### Unresolved Alerts
```sql
SELECT level, type, chain, address, message,
  FROM_UNIXTIME(created_at) as created
FROM system_alert WHERE status=0 ORDER BY created_at DESC LIMIT 20;
```

### Fee Wallet Balance Check
```sql
SELECT chain, address, balance_cache,
  FROM_UNIXTIME(balance_updated_at) as last_updated
FROM fee_wallet WHERE status=1;
```

### Address Scan Lag
```sql
SELECT chain, status,
  COUNT(*) as total,
  ROUND(AVG(UNIX_TIMESTAMP() - last_scan_time)) as avg_lag_seconds,
  MAX(UNIX_TIMESTAMP() - last_scan_time) as max_lag_seconds
FROM wallet_address GROUP BY chain, status;
```

### Task Retry Status
```sql
SELECT chain, symbol, retry_count, COUNT(*) as cnt
FROM collect_task WHERE status=7 GROUP BY chain, symbol, retry_count;
```

## Log Files

```bash
tail -f logs/app.log          # Application log
tail -f logs/error.log        # Errors only
tail -f logs/collect.log      # Task execution
tail -f logs/transaction.log  # TX broadcast/confirm
```
