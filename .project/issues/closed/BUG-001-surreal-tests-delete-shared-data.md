# BUG-001 — Surreal integration test deletes shared production tables

> **Category:** BUG
> **Severity:** Critical
> **Status:** open
> **Filed:** 2026-06-12
> **Affected:** `tests/test_surreal_chain.py:64`, `tests/test_surreal_chain.py:67`, `tests/test_surreal_chain.py:351`

## Summary

The live SurrealDB chain test connects to the default `antigravity/unified` database and deletes every record in three shared DecisionMemory tables. Running the test can destroy real decision and audit data.

## Evidence

`SurrealDatabase()` uses the normal environment/default namespace and database. The test then executes:

```python
DELETE FROM tm_audit_chain
DELETE FROM tm_audit_roots
DELETE FROM tm_decision_records
```

both during setup and cleanup, without checking that the database is disposable. This test was run on 2026-06-12 and emptied those tables.

## Root cause

The integration test treats shared tables as isolated fixtures instead of using a dedicated test namespace/database or deleting only records created by the test.

## Suggested fix

- Require an explicit test database such as `antigravity/decisionmemory_test`.
- Refuse to run unless `SURREAL_DB` matches an allowlisted test name.
- Generate a unique run prefix and delete only records carrying that prefix.
- Convert the script into pytest tests with fixtures that verify isolation before mutation.

## Decision

Pending.
