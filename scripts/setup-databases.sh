#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

PYTHON="${PYTHON:-python3}"

if ! command -v "$PYTHON" >/dev/null 2>&1; then
  echo "Python 3.10+ is required." >&2
  exit 1
fi

if [[ ! -x .venv/bin/python ]]; then
  "$PYTHON" -m venv .venv
fi

.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -e '.[test,surreal]'

if ! .venv/bin/python -c 'import lancedb' >/dev/null 2>&1; then
  .venv/bin/python -m pip install lancedb
fi

if command -v surreal >/dev/null 2>&1; then
  echo "SurrealDB: $(surreal version 2>/dev/null || echo installed)"
elif [[ "${INSTALL_SURREAL:-1}" == "0" ]]; then
  echo "SurrealDB is missing and INSTALL_SURREAL=0; skipping installation."
else
  case "$(uname -s)" in
    Darwin)
      if command -v brew >/dev/null 2>&1; then
        echo "Installing SurrealDB with Homebrew..."
        brew install surrealdb/tap/surreal
      else
        echo "Homebrew is required for the automated macOS install." >&2
        echo "Install from https://brew.sh/ or follow https://surrealdb.com/install" >&2
        exit 1
      fi
      ;;
    Linux)
      if ! command -v curl >/dev/null 2>&1; then
        echo "curl is required to run SurrealDB's official installer." >&2
        exit 1
      fi
      echo "Installing SurrealDB with the official installer..."
      curl -sSf https://install.surrealdb.com | sh
      ;;
    *)
      echo "Automated SurrealDB installation is not supported on this OS." >&2
      echo "Follow https://surrealdb.com/install" >&2
      exit 1
      ;;
  esac
fi

if command -v cargo >/dev/null 2>&1; then
  cargo build --locked --release \
    --manifest-path database-manager/db-cli-optimized/Cargo.toml
else
  echo "Cargo not found; skipping the optional database-manager Rust CLI."
  echo "Install Rust from https://rustup.rs/ and rerun this script to build it."
fi

cat <<'EOF'

Setup complete.

Activate Python:
  source .venv/bin/activate

Start SurrealDB:
  ./scripts/start-surreal.sh

Start the DecisionMemory MCP server:
  python -m decisionmemory
EOF
