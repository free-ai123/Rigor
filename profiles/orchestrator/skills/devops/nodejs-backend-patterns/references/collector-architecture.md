# Multi-Chain Collector Service — Architecture Reference

> Absorbed from `nodejs-collector-pattern` (2026-05-20). Single-process Node.js service with 6 cron jobs + health check, MySQL task queue, dual databases, AES-256-GCM encryption. ETH/BSC/TRON auto-collection.

## Core Architecture

6 cron jobs + health check job, MySQL task queue, dual databases (biz read-only + collector read-write). All configurable parameters in `.env` organized by chain and functional section (12 sections, ~78 vars).

## Required Files (38 JS files)

```
collector-service/
├── app.js                          # Entry: init DB pools, start 7 jobs, handle SIGTERM/SIGINT
├── config/
│   ├── index.js                    # Re-exports: db config, CHAIN_MAP, envConfig
│   └── envConfig.js                # Unified config from .env: per-chain params, jobSchedule,
│                                   #   batchSize, lockAndRetry, rpcLimit, gasLimits, alert
├── db/
│   ├── index.js                    # Re-export both pools + closePools()
│   ├── collectorDb.js              # initCollectorPool / getCollectorPool / closeCollectorPool
│   └── bizDb.js                    # initBizPool / getBizPool / closeBizPool
├── adapters/
│   ├── evmAdapter.js               # ethers.js v6: balance, token, send, receipt, blockNumber
│   └── tronAdapter.js              # tronweb: same interface + feeLimit
├── services/
│   ├── collectTaskService.js       # Create tasks, update status, lock/unlock (MySQL locks)
│   ├── collectService.js           # Execute collection: decrypt key, build+sign+send tx
│   ├── feeService.js               # Top up fee wallet → user address
│   ├── balanceService.js           # Scan main + token balance, update address_balance
│   ├── addressSyncService.js       # Sync biz DB status=1 addresses → wallet_address
│   ├── monitorService.js           # Check tx receipts, confirmations, pending timeout
│   ├── nonceService.js             # EVM nonce: SELECT FOR UPDATE, max(local, chain_pending)
│   ├── gasService.js               # Gas from .env: EIP-1559 (ETH), gasPrice (BSC)
│   ├── rpcService.js               # RPC pool: priority selection, Bottleneck rate limit
│   ├── walletGenerateService.js    # Generate EVM/TRON wallets, encrypt + save
│   ├── alertService.js             # Write to system_alert + send Feishu webhook card
│   ├── feishuAlert.js              # Feishu interactive card builder + HTTP POST + cooldown
│   ├── healthService.js            # 7-dim health check: DB/RPC/balance/backlog/fail/pending/alerts
│   └── taskLogService.js           # Write to task_status_log
├── jobs/
│   ├── index.js                    # Re-export all jobs
│   ├── addressSyncJob.js           # Sync biz DB → wallet_address (every 15s)
│   ├── balanceScanJob.js           # Scan balances, create tasks at threshold (every 60s)
│   ├── collectJob.js               # Execute MAIN_COLLECT and TOKEN_COLLECT (every 10s)
│   ├── feeJob.js                   # Top up insufficient fee (every 10s)
│   ├── monitorJob.js               # Check tx confirmations, handle timeouts (every 15s)
│   ├── retryJob.js                 # Retry failed tasks, exponential backoff (every 30s)
│   └── healthCheckJob.js           # 7-dim health check, auto-alert on critical (every 5min)
├── utils/
│   ├── crypto.js                   # AES-256-GCM: encryptPrivateKey / decryptPrivateKey
│   ├── amount.js                   # toWei/fromWei (decimal.js), aliases: toRaw/fromRaw
│   └── logger.js                   # winston: 4 log files, redact private keys/0x64hex
├── constants/
│   └── status.js                   # TASK_PENDING=0..TASK_SKIPPED=8, TX_STATUS, WALLET_STATUS
├── scripts/
│   ├── check_status.js             # Manual: show task stats, alerts, pending, RPC, recent tx
│   └── test_all.js                 # Full end-to-end verification
├── package.json                    # ethers tronweb mysql2 decimal.js dotenv winston node-cron uuid bottleneck
├── .env                            # 12 categorized sections, ~78 config vars
├── .gitignore
└── README.md
```

## .env Configuration (12 Sections)

```ini
# [1] 基础环境     NODE_ENV, WORKER_ID, LOG_LEVEL
# [2] 数据库配置   BIZ_DB_*, COLLECTOR_DB_* (host/port/user/password/name/poolSize)
# [3] 私钥加密     WALLET_MASTER_KEY (64-char hex, 32 bytes)
# [4] ETH 主网     ETH_COLLECT_ADDRESS, ETH_FEE_WALLET_PRIVATE_KEY, ETH_RPC_URL, ETH_RPC_URL_2, ETH_MAX_FEE_PER_GAS, ETH_MAX_PRIORITY_FEE, ETH_MIN_COLLECT, ETH_USDT_MIN_COLLECT, ETH_MIN_FEE_BALANCE, ETH_FEE_TOPUP_AMOUNT, ETH_RESERVE_MAIN, ETH_CONFIRM_BLOCKS, ETH_TX_TIMEOUT
# [5] BSC 链       (same as ETH, with BSC_MAX_GAS_PRICE instead of EIP-1559)
# [6] TRON 链      (same as ETH, with TRON_FEE_LIMIT instead of gas)
# [7] 公共Gas限制  MAIN_TRANSFER_GAS_LIMIT(21000), TOKEN_TRANSFER_GAS_LIMIT(80000), FEE_TOPUP_GAS_LIMIT(65000)
# [8] 定时任务     JOB_ADDRESS_SYNC_INTERVAL(15), JOB_BALANCE_SCAN_INTERVAL(60), JOB_COLLECT_INTERVAL(10), JOB_FEE_INTERVAL(10), JOB_MONITOR_INTERVAL(15), JOB_RETRY_INTERVAL(30)
# [9] 批处理大小   BATCH_ADDRESS_SYNC(500), BATCH_COLLECT(10), BATCH_FEE(10), BATCH_MONITOR(50), BATCH_RETRY(20), BATCH_SCAN_ETH(100), BATCH_SCAN_BSC(200), BATCH_SCAN_TRON(100)
# [10] 锁与重试    TASK_LOCK_TTL(60), MAX_RETRY(5), RETRY_INTERVALS(60,300,900,3600)
# [11] RPC限流     RPC_MAX_CONCURRENT(5), RPC_MIN_TIME_MS(150)
# [12] 告警        ALERT_WEBHOOK_URL, ALERT_THRESHOLD_RPC_FAIL(3), ALERT_COOLDOWN_SECONDS(300)
```

## Database Tables (15 in collector DB)

wallet_key, wallet_address, chain_config, asset_config, fee_wallet, address_balance, collect_task, collect_task_open, chain_transaction, nonce_state, gas_policy, rpc_endpoint, task_status_log, system_alert, collector_state

## Key Patterns

1. **Task locking**: `UPDATE collect_task SET locked_by=?, locked_until=? WHERE id=? AND status IN (0,3) AND (locked_until IS NULL OR locked_until < UNIX_TIMESTAMP())`
2. **Nonce allocation**: Transaction + `SELECT FOR UPDATE` on nonce_state, `max(local_next_nonce, chain_pending_nonce)`
3. **Idempotency**: `collect_task_open` with `UNIQUE(task_key)` where task_key = `chain:symbol:from_address`
4. **RPC failover**: Query rpc_endpoint ordered by priority ASC, skip status=2 (unhealthy), increment fail_count on error
5. **Pending timeout**: Set `expire_at = now + timeout` on broadcast; `UPDATE SET status=4 WHERE expire_at < NOW()`
6. **Amount precision**: Always store both `amount` (DECIMAL) and `raw_amount` (VARCHAR wei/sun)
7. **AES-256-GCM**: Store cipher (TEXT hex) + iv (VARCHAR 12-byte hex) + tag (VARCHAR 16-byte hex) separately
8. **Fee check before token collection**: Compare main coin balance against minFeeBalance from .env
9. **Config-driven**: All thresholds, gas params, confirm blocks, timeouts read from .env via envConfig — zero hardcoded values
10. **Feishu alert**: alertService.createAlert() writes to DB + sends Feishu webhook card (async, with 300s cooldown per alert type)
11. **Health check**: 7 dimensions checked every 5min — DB connectivity, RPC availability, fee wallet balance, task backlog (>50 stuck), failed tasks (>5/hour), pending tx (>20), unresolved alerts

## Pitfalls (from collector build sessions)

- **Worker schema drift**: Backend workers may modify DB field names from the spec. Always verify table structure with `DESCRIBE` after DB tasks complete.
- **Worker code interface drift**: Workers also change function exports, module names, and constant values. After code tasks complete, run `node -e "Object.keys(require('./module'))"` to verify expected exports exist.
- **MySQL password reset**: Devops tasks may reset root password. If `mysql -uroot -p<old>` fails, use skip-grant-tables mode to reset.
- **Terminal blocks**: Workers with blocked terminal access cannot install npm deps or verify DB connections. Write files directly to persistent project directory.
- **Scratch workspace GC**: Each worker's files are deleted on task completion. Copy to `~/projects/<name>/` immediately after each task completes.
