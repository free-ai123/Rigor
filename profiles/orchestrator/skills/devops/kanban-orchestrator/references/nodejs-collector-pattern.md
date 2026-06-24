# Node.js Multi-Chain Collector Service — Reference Pattern

## Core Architecture

Single-process Node.js service with 6 cron jobs, MySQL task queue, dual databases.

## Required Files (32 JS files)

```
collector-service/
├── app.js                          # Entry: init DB pools, start 6 jobs, handle SIGTERM/SIGINT
├── config/
│   ├── index.js                    # Load .env via dotenv, export db config
│   └── chains.js                   # Chain params (chainId, decimals, confirmBlocks)
├── db/
│   ├── index.js                    # Re-export both pools + closePools()
│   ├── collectorDb.js              # mysql2 pool for collector DB (read-write)
│   └── bizDb.js                    # mysql2 pool for business DB (read-only)
├── adapters/
│   ├── evmAdapter.js               # ethers.js: getBalance, getTokenBalance, sendNative, sendToken, getReceipt, getBlockNumber
│   └── tronAdapter.js              # tronweb: same interface + feeLimit support
├── services/
│   ├── collectTaskService.js       # Create tasks, update status, lock/unlock with MySQL locks
│   ├── collectService.js           # Execute collection: decrypt key, build+sign+send tx
│   ├── feeService.js               # Top up fee wallet → user address
│   ├── balanceService.js           # Scan main + token balance, update address_balance table
│   ├── addressSyncService.js       # Sync biz DB status=1 addresses to collector wallet_address
│   ├── monitorService.js           # Check tx receipts, confirmations, pending timeout
│   ├── nonceService.js             # EVM nonce: SELECT FOR UPDATE, max(local, chain_pending)
│   ├── gasService.js               # Gas strategy: EIP-1559 for ETH, gasPrice for BSC
│   ├── rpcService.js               # RPC pool: priority-based selection, Bottleneck rate limit
│   ├── walletGenerateService.js    # Generate EVM/TRON wallets, encrypt + save
│   ├── alertService.js             # Write to system_alert table
│   └── taskLogService.js           # Write to task_status_log table
├── jobs/
│   ├── index.js                    # Re-export all jobs
│   ├── addressSyncJob.js           # Every 15s: sync biz DB → wallet_address
│   ├── balanceScanJob.js           # Every 60s: scan balances, create tasks at threshold
│   ├── collectJob.js               # Every 10s: execute MAIN_COLLECT and TOKEN_COLLECT tasks
│   ├── feeJob.js                   # Every 10s: top up insufficient fee for TOKEN_COLLECT
│   ├── monitorJob.js               # Every 15s: check tx confirmations, handle timeouts
│   └── retryJob.js                 # Every 30s: retry failed tasks with exponential backoff
├── utils/
│   ├── crypto.js                   # AES-256-GCM encrypt/decrypt private keys
│   ├── amount.js                   # toWei/fromWei with decimal.js precision
│   └── logger.js                   # winston: 4 log files, redact private keys
├── constants/
│   └── status.js                   # All status code constants (task, wallet, transaction)
├── package.json                    # ethers tronweb mysql2 decimal.js dotenv winston node-cron uuid bottleneck
├── .env                            # BIZ_DB_*, COLLECTOR_DB_*, WALLET_MASTER_KEY, WORKER_ID
└── .gitignore                      # node_modules, .env, logs/
```

## Database Tables (15 in collector DB)

wallet_key, wallet_address, chain_config, asset_config, fee_wallet,
address_balance, collect_task, collect_task_open, chain_transaction,
nonce_state, gas_policy, rpc_endpoint, task_status_log, system_alert,
collector_state

## Key Patterns

1. **Task locking**: `UPDATE collect_task SET locked_by=?, locked_until=? WHERE id=? AND locked_until < NOW()`
2. **Nonce allocation**: Transaction + `SELECT FOR UPDATE` on nonce_state row
3. **Idempotency**: `collect_task_open` with `UNIQUE(task_key)` where task_key = `chain:symbol:from_address`
4. **RPC failover**: Sort by priority, increment fail_count, mark unhealthy after N failures
5. **Pending timeout**: Set `expire_at` on broadcast, `UPDATE SET status=4 WHERE expire_at < NOW()`
6. **Amount precision**: Always store both `amount` (decimal) and `raw_amount` (string wei/sun)
