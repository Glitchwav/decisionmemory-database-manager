# BUG-002 — Backend factory is bypassed by production entry points

> **Category:** BUG
> **Severity:** High
> **Status:** open
> **Filed:** 2026-06-12
> **Affected:** `src/decisionmemory/mcp_server.py:16`, `src/decisionmemory/mcp_server.py:37`, `src/decisionmemory/journal.py:27`, `src/decisionmemory/state.py:27`, `src/decisionmemory/repositories/decision.py:62`, `src/decisionmemory/db_factory.py:13`

## Summary

Setting `DECISIONMEMORY_BACKEND=surreal` does not switch the main application to SurrealDB. Core production paths instantiate the SurrealDB `Database` class directly and never call the new factory.

## Evidence

The MCP server imports `Database` and initializes `_db = Database()`. Journal, state, repository, replay, simulation, and other paths follow the same pattern. A runtime probe with `DECISIONMEMORY_BACKEND=surreal` still produced SurrealDB-backed `DecisionJournal` and `StateManager` instances.

## Root cause

The backend factory was added alongside the existing constructors, but dependency creation was not centralized or migrated.

## Suggested fix

- Establish one canonical `get_database()` implementation.
- Replace direct default construction in production services with the factory.
- Preserve explicit dependency injection for tests and callers passing a database instance.
- Add a runtime test asserting the MCP server, journal, state manager, and repository use `SurrealDatabase` when selected.
- Decide explicitly whether replay and simulation support alternate backends or reject them clearly.

## Decision

Pending.
