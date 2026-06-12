# QA-001 — Surreal backend tests are not valid isolated pytest coverage

> **Category:** QA
> **Severity:** Medium
> **Status:** open
> **Filed:** 2026-06-12
> **Affected:** `tests/test_surreal_backend.py:40`, `tests/test_surreal_backend.py:117`, `tests/test_surreal_backend.py:663`, `tests/test_surreal_chain.py:36`

## Summary

The new Surreal tests are custom executable scripts rather than reliable pytest coverage. One file requests an undefined `db` fixture, hard-codes a developer path, and creates the database only in `main`; the other exposes no pytest test functions.

## Evidence

Running `tests/test_surreal_backend.py` directly produced 23/23 passing checks, and `tests/test_surreal_chain.py` directly produced 52/52. Under pytest, however, backend test functions require a fixture that does not exist, while the chain file collects no test cases. The repository virtual environment also lacks pytest.

## Root cause

The checks were written as manual validation harnesses and placed under `tests/` without conversion to the project's test framework and isolation conventions.

## Suggested fix

- Convert both files to normal pytest tests and fixtures.
- Remove absolute developer paths.
- Mark live database checks as `integration`.
- Require a disposable test database and skip safely when it is unavailable.
- Add the optional Surreal dependency to the CI integration job.
- Keep destructive operations scoped to uniquely tagged records.

## Decision

Pending.
