# DecisionMemory + Database Manager

Persistent, outcome-aware memory for AI decision agents, backed by SurrealDB.

DecisionMemory records decisions and outcomes, recalls relevant prior decisions, tracks behavioral state, and exposes its workflows through MCP, REST, and CLI interfaces. The repository includes a lightweight SurrealDB CLI and an experimental LanceDB/FastEmbed component.

## What It Includes

- Five decision-memory types: episodic, semantic, procedural, affective, and prospective
- Outcome-weighted and optional vector-assisted recall
- SHA-256 decision audit chains and daily Merkle roots
- Decision-Making plans, behavioral analysis, legitimacy checks, and strategy validation
- SurrealDB tables prefixed with `tm_`
- MCP server, REST API, and management CLI
- Database-manager skill instructions and Rust source

## Quick Start

Requirements: Python 3.10+, `curl`, and optionally Rust/Cargo.

```bash
./scripts/setup-databases.sh
source .venv/bin/activate
python -m decisionmemory
```

The setup script:

1. Creates `.venv` and installs DecisionMemory with test and SurrealDB support.
2. Installs Python LanceDB if it is missing.
3. Installs the `surreal` server with Homebrew on macOS or SurrealDB's official installer on Linux when absent.
4. Builds the lightweight database-manager CLI when Cargo is available.

Start a local authenticated SurrealDB instance in another terminal:

```bash
./scripts/start-surreal.sh
```

Set `INSTALL_SURREAL=0` before setup to skip automatic SurrealDB installation.

Then configure the shared database:

```bash
cp .env.example .env
export SURREAL_USER=root
export SURREAL_PASS=secret
export SURREAL_NS=antigravity
export SURREAL_DB=unified
python -m decisionmemory
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

- The SurrealDB integration is new and should receive further production hardening.
- LanceDB is packaged as an optional SDK and experimental Rust prototype, not a unified production index.
- Strategy evolution and decision-quality research results are experimental and are not evidence of decision-making positive outcomes.
- MT5 remains the primary documented provider connector.

See [LIMITATIONS.md](LIMITATIONS.md) and [.project/issues/open](.project/issues/open) for tracked constraints.

## Safety

This is research and engineering software, not decision advice. Test with disposable databases and paper decision data before connecting real decision-making workflows.

## License

DecisionMemory is provided under the [MIT License](LICENSE). Third-party crates, Python packages, SurrealDB, LanceDB, and downloaded embedding models retain their own licenses.
