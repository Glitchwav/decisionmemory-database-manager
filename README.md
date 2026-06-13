# DecisionMemory + Database Manager

Persistent, outcome-aware memory for AI decision agents.

DecisionMemory stores authoritative application data in SQLite. It records decisions and outcomes, recalls relevant prior decisions, tracks behavioral state, and exposes its workflows through MCP, REST, and CLI interfaces. An optional database-manager integration publishes a fail-open secondary copy to persistent SurrealDB and supports offline semantic indexing with LanceDB.

## What It Includes

- Five decision-memory types: episodic, semantic, procedural, affective, and prospective
- Outcome-weighted and optional vector-assisted recall
- SHA-256 decision audit chains and daily Merkle roots
- Decision-Making plans, behavioral analysis, legitimacy checks, and strategy validation
- SQLite transactions and isolated local databases
- Optional, fail-open publication of decisions, episodic memories, embeddings, outcomes, session state, and reference relationships to SurrealDB
- Non-destructive LanceDB candidate-index workflow for semantic validation
- MCP server, REST API, and management CLI
- Database-manager skill instructions and Rust source

## Quick Start

Requirements: Python 3.10+.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[test]'
python -m decisionmemory
```

SQLite is initialized automatically. By default, data is stored under `~/.decisionmemory/decisionmemory.db` when that file exists, otherwise `data/decisionmemory.db`. Set `DECISIONMEMORY_DB` to choose another path.

## Database Manager Setup

Install the optional Python database client and local tooling:

```bash
./scripts/setup-databases.sh
source .venv/bin/activate
```

When the database-manager service is installed on the backup drive, start and verify persistent SurrealDB with:

```bash
SM="/Volumes/Backup Drive/scratch/service-manager/sm"
"$SM" start surrealdb
"$SM" status surrealdb
```

Expected status:

```text
surreal: Running (persistent backup-drive storage)
```

The verified service binds to `127.0.0.1:8000`, runs without authentication, and stores data under:

```text
/Volumes/Backup Drive/scratch/database-manager/SurrealDB
```

Use `"$SM" restart surrealdb` for a controlled restart. The status check verifies the bind address, authentication mode, and persistent data path rather than only checking whether port 8000 is open.

Do not run `scripts/start-surreal.sh` at the same time as the shared database-manager service. That script uses separate configuration and will contend for port 8000.

To publish a secondary graph copy while retaining SQLite:

```bash
cp .env.example .env
export DECISIONMEMORY_SECONDARY_STORE=surreal
export SURREAL_HOST=http://127.0.0.1
export SURREAL_PORT=8000
export SURREAL_NS=antigravity
export SURREAL_DB=unified
unset SURREAL_USER SURREAL_PASS
python -m decisionmemory
```

Set both `SURREAL_USER` and `SURREAL_PASS` only when connecting to an authenticated SurrealDB instance. Supplying only one credential is rejected.

The publisher runs after successful SQLite commits. SurrealDB failures are logged and do not roll back SQLite. Reads, audit chains, reporting, and application tests continue to use SQLite.

The REST API also defaults to port `8000`, so run it on another port when SurrealDB is local:

```bash
uvicorn decisionmemory.server:app --host 127.0.0.1 --port 8001
```

## Database Manager

`database-manager/db-cli-optimized` is a small Rust client for SurrealDB keyword search, graph operations, and raw SurrealQL:

```bash
cargo build --locked --release --manifest-path database-manager/db-cli-optimized/Cargo.toml
database-manager/db-cli-optimized/target/release/db-cli-optimized \
  search --keyword breakout --table memory
```

DecisionMemory does not write directly to the live LanceDB table. Semantic indexes are built offline from SurrealDB records so they can be validated before use.

The non-destructive indexing process is:

1. Export records to a new JSONL file.
2. Build a new LanceDB directory and table.
3. Validate record counts, unique IDs, and representative semantic searches.
4. Switch the configured path only after validation succeeds.
5. Retain the previous directory for rollback.

Repeated ingestion into the same table is not supported because the current FFI appends records. Always build a fresh candidate index instead.

This workflow has been verified with the real CoreML embedding model, Rust FFI, and LanceDB without changing the live index.

No user databases, model caches, compiled binaries, or private memory records are included.

## Tests

Run the core suite:

```bash
python -m pytest -q -m "not integration"
```

Run live SurrealDB tests only against the disposable `decisionmemory_test` database:

```bash
SURREAL_USER='' SURREAL_PASS='' SURREAL_DB_TEST=decisionmemory_test \
  python -m pytest tests/test_surreal_backend.py tests/test_surreal_chain.py \
  -q -m integration
```

The verified live integration suite contains 43 tests.

## Current Limits

- SurrealDB publication is optional and currently has no durable retry queue.
- Existing SQLite records need an explicit backfill before they appear in SurrealDB or a candidate semantic index.
- LanceDB indexing is asynchronous and requires a fresh-directory rebuild to avoid duplicate IDs.
- Semantic quality depends on descriptive context and reflection appearing early in exported text because the CoreML model uses the first 128 WordPiece tokens.
- The legacy full SurrealDB database implementation remains for compatibility testing but is not selected by the application factory.

See [LIMITATIONS.md](LIMITATIONS.md) and [.project/issues/open](.project/issues/open) for tracked constraints.

## Safety

This is research and engineering software, not decision advice. Test with disposable databases and paper decision data before connecting real decision-making workflows.

## License

DecisionMemory is provided under the [MIT License](LICENSE). Third-party crates, Python packages, SurrealDB, LanceDB, and downloaded embedding models retain their own licenses.
