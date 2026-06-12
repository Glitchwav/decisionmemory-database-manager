# BUG-003 — Surreal authentication defaults conflict with database-manager

> **Category:** BUG
> **Severity:** High
> **Status:** open
> **Filed:** 2026-06-12
> **Affected:** `src/decisionmemory/db_surreal.py:364`, `src/decisionmemory/db_surreal.py:366`, `src/decisionmemory/db_surreal.py:373`

## Summary

DecisionMemory always attempts SurrealDB authentication using default `root/root` credentials. Database-manager's normal local deployment is unauthenticated and only sends credentials when both environment variables are configured.

## Evidence

`SurrealDatabase.__init__` defaults `SURREAL_USER` and `SURREAL_PASS` to `root`, then unconditionally calls `signin`. The database-manager skill documents optional Basic authentication and an unauthenticated default.

## Root cause

The new client independently defined connection behavior instead of following database-manager's established environment contract.

## Suggested fix

- Leave username and password unset by default.
- Call `signin` only when both `SURREAL_USER` and `SURREAL_PASS` are non-empty.
- Fail clearly when only one credential is supplied.
- Add tests for unauthenticated, authenticated, and partially configured connections.
- Document the shared namespace/database defaults.

## Decision

Pending.
