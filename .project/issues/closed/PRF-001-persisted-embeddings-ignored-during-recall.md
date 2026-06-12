# PRF-001 — Recall ignores persisted embeddings and recomputes candidates

> **Category:** PRF
> **Severity:** Medium
> **Status:** deferred
> **Filed:** 2026-06-12
> **Updated:** 2026-06-12
> **Affected:** `src/decisionmemory/mcp_server.py:470`, `src/decisionmemory/mcp_server.py:539`, `src/decisionmemory/mcp_server.py:545`, `src/decisionmemory/db_surreal.py:818`

## Summary

Hybrid recall does not propagate stored episodic embeddings into candidate objects, so it recomputes embeddings for every candidate on each recall.

## Deferred Reason

Requires changes to `mcp_server.py` (core MCP tools), which is off-limits per CLAUDE.md unless explicitly required by ROADMAP. The SurrealDB backend now correctly stores and returns embedding fields, so the fix is limited to the recall candidate construction path in mcp_server.py.

## Resolution Path

When ROADMAP authorizes MCP tool changes:
1. Carry validated stored embeddings into recall candidates from `query_episodic` results
2. Recompute only when embedding is missing or schema version changed
3. Add test asserting second recall performs no candidate re-embedding
