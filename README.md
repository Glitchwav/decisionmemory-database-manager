# DecisionMemory + Database Manager

Persistent, outcome-aware memory for AI decision agents.

DecisionMemory records decisions and outcomes, recalls relevant prior decisions, tracks behavioral state, and exposes its workflows through MCP, REST, and CLI interfaces.

## What It Includes

- Five decision-memory types: episodic, semantic, procedural, affective, and prospective
- Outcome-weighted and optional vector-assisted recall
- SHA-256 decision audit chains and daily Merkle roots
- Decision-Making plans, behavioral analysis, legitimacy checks, and strategy validation
- MCP server, REST API, and management CLI
- Database-manager skill instructions and Rust source

## Database Architecture

Each engine has a distinct role. They are not interchangeable.

**SQLite** — primary application storage. Handles transactions, isolated test databases, reporting, audit chains, and all existing SQL-heavy workflows. This is the default and requires no external services.

**SurrealDB** — optional shared graph store for relationships between decisions, memories, agents, sessions, concepts, and outcomes. Activate it explicitly when you need graph-oriented database-manager features. Integrated through a dedicated adapter or synchronization layer, not through SQL translation or the existing `Database` alias. The existing `db_surreal.py` can serve as an optional secondary-store adapter, but it does not implement SQLite compatibility.

**LanceDB** — semantic/vector recall. Embeds and searches decision memories by meaning rather than exact match.

SQLite is always required. SurrealDB and LanceDB are optional and activate independently.

## Quick Start

Requirements: Python 3.10+, `curl`, and optionally Rust/Cargo.

```bash
./scripts/setup-databases.sh
source .venv/bin/activate
python -m decisionmemory
```

The setup script:

1. Creates `.venv` and installs DecisionMemory with test support.
2. Installs Python LanceDB if it is missing.
3. Installs the `surreal` server with Homebrew on macOS or SurrealDB's official installer on Linux when absent (only needed if you want the graph store).
4. Builds the lightweight database-manager CLI when Cargo is available.

### SQLite (default, no extra setup)

SQLite works out of the box. All core functionality — storage, transactions, audit chains, reporting — runs against SQLite with no external services.

```bash
cp .env.example .env
python -m decisionmemory
```

### SurrealDB (optional graph store)

Start a local authenticated SurrealDB instance in another terminal:

```bash
./scripts/start-surreal.sh
```

Set `INSTALL_SURREAL=0` before setup to skip automatic SurrealDB installation.

Then configure the graph store:

```bash
export SURREAL_USER=root
export SURREAL_PASS=secret
export SURREAL_NS=antigravity
export SURREAL_DB=unified
```

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

`database-manager/lancedb-hybrid` is included as experimental source only. It uses LanceDB and FastEmbed but still contains prototype command handling. It is not wired into DecisionMemory's runtime and should not be presented as production-ready.

No user databases, model caches, compiled binaries, or private memory records are included.

## Tests

Core tests:

```bash
python -m pytest tests -q
```

SurrealDB integration tests use the disposable `decisionmemory_test` database and skip when SurrealDB is unavailable:

```bash
python -m pytest tests/test_surreal_backend.py tests/test_surreal_chain.py -q -m integration
```

## Current Limits

- SurrealDB integration is optional and should receive further production hardening when enabled.
- LanceDB is packaged as an optional SDK and experimental Rust prototype, not a unified production index.
- Strategy evolution and decision-quality research results are experimental and are not evidence of decision-making positive outcomes.
- MT5 remains the primary documented provider connector.

See [LIMITATIONS.md](LIMITATIONS.md) and [.project/issues/open](.project/issues/open) for tracked constraints.

## Safety

This is research and engineering software, not decision advice. Test with disposable databases and paper decision data before connecting real decision-making workflows.

## License

DecisionMemory is provided under the [MIT License](LICENSE). Third-party crates, Python packages, SurrealDB, LanceDB, and downloaded embedding models retain their own licenses.
