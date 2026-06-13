# OPS-001 - Running SurrealDB does not use the backup-drive configuration

> **Category:** OPS
> **Severity:** High
> **Status:** resolved
> **Filed:** 2026-06-12
> **Resolved:** 2026-06-12
> **Affected:** `/Volumes/Backup Drive/scratch/service-manager`, local port 8000

## Summary

The service manager reports SurrealDB as running, but the live process is an
authenticated in-memory server rather than the persistent backup-drive service.

## Evidence

The live command is:

```text
/opt/homebrew/bin/surreal start --bind 0.0.0.0:8000 -u root -p root memory
```

The database-manager service definition expects persistent storage under:

```text
/Volumes/Backup Drive/scratch/database-manager/SurrealDB
```

The live database has the DecisionMemory table definitions but no records.
Unauthenticated queries return HTTP 403. The service manager status check only
checks the process and port, so it does not detect the configuration mismatch.

## Required Fix

- Stop the in-memory process only after confirming it contains no data that must
  be preserved.
- Start SurrealDB through the backup-drive service definition.
- Verify namespace, database, authentication mode, and persistent data path with
  a scoped database query.
- Move the DecisionMemory REST API off port 8000 when both services run locally.
- Strengthen the service health check to validate configuration, not only PID
  and port availability.

## Resolution

- Exported the authenticated in-memory database before stopping it.
- Exported the existing persistent database before merging.
- Started SurrealDB through service-manager with persistent RocksDB storage at
  `/Volumes/Backup Drive/scratch/database-manager/SurrealDB`.
- Imported the in-memory records and verified counts after restart.
- Verified an end-to-end SQLite decision and episodic write, Surreal secondary
  publication, and embedding update, then removed the disposable probe records.
- Ran all 43 live SurrealDB integration tests successfully.
- Added a working `restart surrealdb` command to service-manager.
- Strengthened service-manager status/start checks to verify the configured
  bind address, unauthenticated mode, and backup-drive data path.

Backups:

```text
/Volumes/Backup Drive/scratch/database-manager/exports/unified-memory-20260612-220209.surql
/Volumes/Backup Drive/scratch/database-manager/exports/unified-persistent-before-merge-20260612-220249.surql
```
