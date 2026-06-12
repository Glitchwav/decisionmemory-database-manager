# ENH-001 — Complete database-manager semantic vector integration

> **Category:** ENH
> **Severity:** Medium
> **Status:** open
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

Pending. Revisit when database-manager data pipeline is rebuilt.
