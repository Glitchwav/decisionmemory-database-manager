---
name: database-manager
description: Use for DecisionMemory persistent storage, SurrealDB setup and queries, LanceDB installation checks, semantic-index experiments, database health checks, and building the packaged database-manager CLIs.
---

# Database Manager

Use SurrealDB for structured DecisionMemory storage and LanceDB for optional local vector experiments.

## First Run

From the repository root:

```bash
./scripts/setup-databases.sh
./scripts/start-surreal.sh
```

Never install dependencies or start a service without telling the user what will be downloaded or launched.

## Backend Configuration

```bash
export SURREAL_HOST=http://localhost
export SURREAL_PORT=8000
export SURREAL_USER=root
export SURREAL_PASS=secret
export SURREAL_NS=antigravity
export SURREAL_DB=unified
```

DecisionMemory uses `tm_`-prefixed tables to coexist with other records.

## Health Checks

```bash
command -v surreal
curl -fsS http://localhost:8000/health
.venv/bin/python -c "import surrealdb, lancedb; print('database SDKs ready')"
```

Build and use the lightweight SurrealDB CLI:

```bash
cargo build --locked --release \
  --manifest-path database-manager/db-cli-optimized/Cargo.toml

database-manager/db-cli-optimized/target/release/db-cli-optimized \
  search --keyword "breakout" --table memory
```

## Safety

- Use a disposable database for integration tests.
- Never delete whole shared tables as test cleanup.
- Do not commit `.env`, databases, LanceDB stores, model caches, or build output.
- Use both `SURREAL_USER` and `SURREAL_PASS`, or neither.
- Keep the REST API off port 8000 when local SurrealDB uses that port.

## LanceDB Status

Python LanceDB is installed by `scripts/setup-databases.sh`.

`database-manager/lancedb-hybrid` is experimental source. It downloads an embedding model on first use and is not yet connected to DecisionMemory's runtime. Do not claim unified vector indexing until its command handling, storage paths, licensing, and integration tests are completed.
