# SEC-001 — User-controlled values are interpolated into SurrealQL

> **Category:** SEC
> **Severity:** High
> **Status:** open
> **Filed:** 2026-06-12
> **Affected:** `src/decisionmemory/db_surreal.py:101`, `src/decisionmemory/db_surreal.py:376`, `src/decisionmemory/db_surreal.py:442`, `src/decisionmemory/db_surreal.py:497`, `src/decisionmemory/db_surreal.py:573`, `src/decisionmemory/db_surreal.py:785`

## Summary

Record IDs and filter values are inserted directly into SurrealQL. Special characters can break valid operations, and hostile values may alter query meaning.

## Evidence

Queries are built with expressions such as `tm_decision_records:{decision_id}` and `strategy = '{strategy}'`. `_q` accepts a `params` argument but does not use it. The SQL compatibility layer also interpolates strings with incomplete escaping. Database-manager separately documents that hyphens and periods require special record-ID handling.

## Root cause

The backend uses ad hoc string construction instead of SurrealDB's structured record IDs, bound variables, or a single validated encoding function.

## Suggested fix

- Use query variables for all field values and filters.
- Use `RecordID` or a rigorously validated/quoted identifier helper for record references.
- Reject unsupported identifiers before executing queries.
- Add adversarial tests covering quotes, backslashes, hyphens, periods, colons, whitespace, Unicode, and injection-shaped input.

## Decision

Pending.
