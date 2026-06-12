#!/usr/bin/env bash
set -euo pipefail

if ! command -v surreal >/dev/null 2>&1; then
  echo "SurrealDB is not installed. See https://surrealdb.com/install" >&2
  exit 1
fi

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DATA_DIR="${SURREAL_DATA_DIR:-$ROOT/.local/surrealdb}"
SURREAL_USER="${SURREAL_USER:-root}"
SURREAL_PASS="${SURREAL_PASS:-secret}"
SURREAL_BIND="${SURREAL_BIND:-127.0.0.1:8000}"

mkdir -p "$DATA_DIR"

echo "Starting SurrealDB at $SURREAL_BIND"
echo "Data directory: $DATA_DIR"
exec surreal start \
  --bind "$SURREAL_BIND" \
  --user "$SURREAL_USER" \
  --pass "$SURREAL_PASS" \
  "rocksdb://$DATA_DIR"
