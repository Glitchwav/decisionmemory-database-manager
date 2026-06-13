# DecisionMemory + Database Manager

Persistent, outcome-aware memory for AI decision agents.

DecisionMemory stores its operational data in SQLite. It records decisions and outcomes, recalls relevant prior decisions, tracks behavioral state, and exposes its workflows through MCP, REST, and CLI interfaces. SurrealDB can receive an optional graph copy for shared database-manager workflows.

## What It Includes

- Five decision-memory types: episodic, semantic, procedural, affective, and prospective
- Outcome-weighted and optional vector-assisted recall
- SHA-256 decision audit chains and daily Merkle roots
- Decision-Making plans, behavioral analysis, legitimacy checks, and strategy validation
- SQLite transactions and isolated local databases
- Optional, fail-open publication to a shared SurrealDB graph
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

## Optional Database Manager Setup

The complete setup script installs the optional SurrealDB client/server, Python LanceDB package, and Rust database-manager CLI when supported:

```bash
./scripts/setup-databases.sh
source .venv/bin/activate
```

Start a local authenticated SurrealDB instance in another terminal:

```bash
./scripts/start-surreal.sh
```

Set `INSTALL_SURREAL=0` before running the setup script to skip automatic SurrealDB installation.

To publish a secondary graph copy while retaining SQLite:

```bash
cp .env.example .env
export DECISIONMEMORY_SECONDARY_STORE=surreal
export SURREAL_USER=root
export SURREAL_PASS=secret
export SURREAL_NS=antigravity
export SURREAL_DB=unified
python -m decisionmemory
```

The publisher mirrors decisions, outcomes, session state, and decision-reference relationships after successful SQLite writes. SurrealDB failures are logged and do not roll back SQLite. Reads, audit chains, reporting, and tests continue to use SQLite.

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

`database-manager/lancedb-hybrid` remains downstream experimental source. DecisionMemory does not synchronously write to LanceDB.

No user databases, model caches, compiled binaries, or private memory records are included.

## Tests

Run the core suite:

```bash
python -m pytest -q -m "not integration"
```

Run live SurrealDB tests only against the disposable `decisionmemory_test` database:

```bash
python -m pytest tests/test_surreal_backend.py tests/test_surreal_chain.py -q -m integration
```

## Current Limits

- SurrealDB publication is optional and currently has no durable retry queue.
- LanceDB is packaged as an optional SDK and experimental Rust prototype, not a unified production index.
- The legacy full SurrealDB database implementation remains for compatibility testing but is not selected by the application factory.
- Strategy evolution and decision-quality research results are experimental and are not evidence of decision-making positive outcomes.
- MT5 remains the primary documented provider connector.

See [LIMITATIONS.md](LIMITATIONS.md) and [.project/issues/open](.project/issues/open) for tracked constraints.

## Safety

This is research and engineering software, not decision advice. Test with disposable databases and paper decision data before connecting real decision-making workflows.

## License

DecisionMemory is provided under the [MIT License](LICENSE). Third-party crates, Python packages, SurrealDB, LanceDB, and downloaded embedding models retain their own licenses.
