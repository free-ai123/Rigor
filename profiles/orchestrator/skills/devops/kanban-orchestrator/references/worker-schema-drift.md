# Worker Schema Drift — Pitfall Reference

## Problem

Backend-engineer workers may modify database schemas, field names, or API contracts from what the user originally specified. They do this when "improving" the design during implementation.

## Concrete Example

User specified `wallet_key` table with these fields:
```
chain, address, address_hex, private_key_cipher, private_key_iv, private_key_tag,
encryption_algo, key_version, status, created_at, updated_at
```

T3 worker replaced it with:
```
key_name, encrypted_key, iv, auth_tag, key_version, algorithm, status,
created_at, updated_at
```

The new schema:
- Removed `chain` and `address` columns (needed for lookups)
- Renamed `private_key_cipher` → `encrypted_key` (code uses the original name)
- Renamed `private_key_iv` → `iv` (code uses the original name)
- Removed `address_hex` column

This caused cascading failures: all downstream code that references these columns fails with "Unknown column" errors.

## Detection

After any database-related task completes:
```bash
mysql -uroot -p<password> <db> -e "DESCRIBE <table_name>;"
```

Compare the actual fields against the spec. Check for:
- Missing columns
- Renamed columns
- Changed data types
- Missing indexes

## Fix

If drift is detected, DROP and recreate the table with the correct schema:
```bash
mysql -uroot -p<password> <db> -e "DROP TABLE IF EXISTS <table>;"
# Then run the correct CREATE TABLE
```

If foreign keys prevent DROP:
```sql
SET FOREIGN_KEY_CHECKS=0;
DROP TABLE IF EXISTS <table>;
DROP TABLE IF EXISTS <referenced_by_table>;
# Recreate both tables in correct order
SET FOREIGN_KEY_CHECKS=1;
```

## Prevention

- Include explicit field names in task descriptions
- Add a verification step: "After creating the table, verify all field names match the spec"
- If the user provided a detailed spec, remind the worker: "Use the exact field names from the spec"
