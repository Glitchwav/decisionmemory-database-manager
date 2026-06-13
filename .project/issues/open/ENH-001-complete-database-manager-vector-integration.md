# ENH-001 — Complete database-manager semantic vector integration

> **Category:** ENH
> **Severity:** Medium
> **Status:** partially resolved
> **Updated:** 2026-06-12
> **Filed:** 2026-06-12
> **Affected:** `src/decisionmemory/embedding.py:25`, `src/decisionmemory/db_surreal.py`, `src/decisionmemory/mcp_server.py:539`

## Summary

DecisionMemory units database-manager's SurrealDB namespace but does not participate in its LanceDB/TriadNative semantic index. Structured storage is integrated; vector search is not.

## Current State (as of 2026-06-12)

- SurrealDB backend fully integrated (13 `tm_*` tables, parameterized queries, 43/43 tests passing)
- DecisionMemory embeddings stored as fields in `tm_episodic_memory`
- No code invokes TriadNative or writes to LanceDB's `vectors_ffi` table
- database-manager has zero data in SurrealDB; TriadNative binary missing; LanceDB data stale

## Options Under Consideration

1. **Standalone (current)** — DecisionMemory keeps its own embedding path. Clean separation.
2. **Extend dump_all.py** — add `tm_episodic_memory` to batch export with `tm_ep:` ID prefix
3. **Direct LanceDB writes** — DecisionMemory writes to LanceDB via Python SDK at insert time
4. **SurrealDB-native vectors** — use SurrealDB v2 vector indexing, eliminate LanceDB
5. **Hybrid shared LanceDB** — both systems write to same table with namespaced IDs

## Decision

Use asynchronous batch indexing. DecisionMemory now publishes episodic records
and subsequent embedding updates to the optional SurrealDB secondary after
SQLite commits. It does not write directly to LanceDB.

## Remaining Operations

- Restore TriadNative and its exporter to an active, non-archived path.
- Extend the exporter to include `tm_episodic_memory`.
- Replace append-only LanceDB ingestion with rebuild-and-switch or true upsert
  behavior before indexing DecisionMemory records.
- Backfill existing SQLite episodic records after persistent SurrealDB is
  running from the backup-drive data path.

## Non-Destructive Validation

Validated on 2026-06-12 using a copy-on-write clone at:

```text
/Volumes/Backup Drive/scratch/database-manager/LanceDB-tests/triad-nondestructive-20260612-221548
```

The cloned Rust FFI accepts an environment-selected LanceDB path. Tests used
new sandbox directories and tables only; the live index retained the same
digest, 1,102 data files, and modification time throughout.

Results:

- Real CoreML embeddings, Rust FFI ingestion, LanceDB storage, and nearest
  neighbor search all worked in isolation.
- Two descriptive synthetic DecisionMemory records ranked correctly for
  distinct breakout and mean-reversion queries.
- Re-ingesting into the same sandbox produced four data files and duplicate
  search results, confirming the append-only risk.
- Rebuilding into a fresh directory produced two files and no duplicates.
- A read-only export of the two live `tm_episodic_memory` records ingested
  successfully into another fresh candidate index.
- Existing live records contain too little descriptive context for a meaningful
  semantic-quality test. Production export should prioritize reflection and
  descriptive context within the first 128 WordPiece tokens.

The approved test and deployment pattern is therefore:

1. Export to a new JSONL file.
2. Build a new LanceDB directory/table.
3. Validate row count, unique IDs, and representative search queries.
4. Switch configuration or an alias only after validation.
5. Retain the previous directory for rollback.
