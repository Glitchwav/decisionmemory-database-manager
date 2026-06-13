# BUG-004 — Decision and audit-chain writes are not atomic

> **Category:** BUG
> **Severity:** High
> **Status:** resolved
> **Resolved:** 2026-06-12
> **Filed:** 2026-06-12
> **Affected:** `src/decisionmemory/db_surreal.py:495`, `src/decisionmemory/db_surreal.py:505`, `src/decisionmemory/db_surreal.py:507`, `src/decisionmemory/db_surreal.py:332`

## Summary

SurrealDB decision insertion commits before the audit-chain entry is created. If chain creation fails, the decision remains stored without an audit record, and retrying does not repair it.

## Evidence

`insert_decision` creates `tm_decision_records:<id>`, then separately calls `ChainBuilder.append`. `SurrealConnection.commit()` and `rollback()` are no-ops because HTTP queries auto-commit. On retry, the existing-decision check returns `True` before checking or restoring the audit entry.

## Root cause

SQLite transaction assumptions were carried into an HTTP-backed compatibility wrapper without implementing a SurrealDB transaction or compensating recovery logic.

## Suggested fix

- Write the decision and chain entry in one SurrealQL transaction.
- Alternatively, detect existing decisions with missing audit entries and repair them deterministically.
- Ensure duplicate IDs with changed immutable content are treated as tampering, not successful idempotency.
- Add fault-injection tests for failure between the two writes.

## Resolution

The compatibility backend now verifies immutable content on duplicate IDs,
repairs missing audit entries deterministically, detects audit tampering, and
removes a newly created decision when audit creation cannot be verified.
Fault-injection tests cover repair, ambiguous commits, and rollback behavior.
