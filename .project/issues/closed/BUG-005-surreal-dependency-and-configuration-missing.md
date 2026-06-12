# BUG-005 — Surreal backend cannot be installed or configured normally

> **Category:** BUG
> **Severity:** Medium
> **Status:** open
> **Filed:** 2026-06-12
> **Affected:** `pyproject.toml:20`, `.env.example:1`, `src/decisionmemory/db_surreal.py:362`

## Summary

The SurrealDB client is imported at runtime but is absent from package dependencies. The backend selection and connection variables are also undocumented, and the default SurrealDB port conflicts with the documented REST API port.

## Evidence

Wheel metadata contains no `Requires-Dist: surrealdb`. A normal package install will raise `ModuleNotFoundError` when the backend is activated. `.env.example` does not describe `DECISIONMEMORY_BACKEND`, `SURREAL_*`, namespace/database selection, or authentication behavior.

## Root cause

The backend implementation was added without completing packaging and operator configuration.

## Suggested fix

- Add a `surreal` optional dependency containing a supported `surrealdb` version.
- Produce a clear error explaining how to install the extra.
- Document all backend and connection variables in `.env.example`.
- Separate or explicitly configure the DecisionMemory REST and SurrealDB ports.
- Add an installation smoke test using the built wheel plus the optional extra.

## Decision

Pending.
