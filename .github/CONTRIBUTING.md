# Contributing

## Setup

```bash
git clone <your-fork-url>
cd decisionmemory-database-manager
./scripts/setup-databases.sh
source .venv/bin/activate
```

SurrealDB integration tests must use a disposable database. Never point test configuration at a database containing user data.

## Checks

```bash
python -m pytest tests -q
ruff check src tests
mypy src/decisionmemory --ignore-missing-imports
python -m build
```

For the optional Rust CLI:

```bash
cargo test --locked --manifest-path database-manager/db-cli-optimized/Cargo.toml
```

## Pull Requests

- Branch from `main`.
- Keep changes scoped and include focused tests.
- Describe database migrations, external downloads, and compatibility effects.
- Do not commit `.env`, credentials, databases, model caches, research output, or build artifacts.
- Use conventional commit prefixes such as `feat:`, `fix:`, `docs:`, and `test:`.

By participating, you agree to follow [CODE_OF_CONDUCT.md](../CODE_OF_CONDUCT.md).
