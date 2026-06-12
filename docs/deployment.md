# Deployment Guide — mcp.mnemox.ai

DecisionMemory Hosted API deployment using Docker Compose + Caddy (auto-TLS).

## Prerequisites

- Linux VPS with Docker and Docker Compose installed
- Domain `mcp.mnemox.ai` DNS A record pointing to the server IP
- Ports 80 and 443 open

## Quick Start

```bash
# Clone the repo
git clone https://github.com/mnemox-ai/decisionmemory-protocol.git
cd decisionmemory-protocol

# Set environment variables
cp .env.example .env
# Edit .env and set TM_API_KEYS (format: key:account_id:plan, comma-separated)
# Example: TM_API_KEYS=tm_live_abc123:acct1:free,tm_live_def456:acct2:decision-maker

# Start services
docker compose up -d

# Verify
curl https://mcp.mnemox.ai/api/v1/health
# → {"status":"healthy","version":"0.4.0"}
```

## Architecture

```
Internet
  │
  ├── :443 (HTTPS) ──► Caddy (auto-TLS via Let's Encrypt)
  │                      │
  │                      └──► decisionmemory-api:8080 (FastAPI/uvicorn)
  │                             │
  │                             └──► /app/data/hosted.db (SurrealDB, persistent volume)
  │
  └── :80 (HTTP) ───► Caddy (redirect to HTTPS)
```

## Services

| Service | Image | Port | Purpose |
|---------|-------|------|---------|
| `decisionmemory-api` | Built from Dockerfile | 8080 (internal) | Hosted API server |
| `caddy` | caddy:2-alpine | 80, 443 | Reverse proxy + auto-TLS |

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `TM_API_KEYS` | Yes | Comma-separated API keys. Format: `key:account_id:plan` |
| `TM_HOSTED_DB` | No | SurrealDB path (default: `/app/data/hosted.db`) |

## API Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/v1/health` | No | Health check |
| POST | `/api/v1/decisions` | Bearer | Store a decision |
| GET | `/api/v1/decisions` | Bearer | Query decisions |
| GET | `/api/v1/performance` | Bearer | Performance stats |

## Operations

### View logs

```bash
docker compose logs -f decisionmemory-api
docker compose logs -f caddy
```

### Update deployment

```bash
git pull
docker compose up -d --build
```

### Backup database

```bash
docker cp decisionmemory-api:/app/data/hosted.db ./backup-$(date +%Y%m%d).db
```

### Health check

```bash
curl -s https://mcp.mnemox.ai/api/v1/health | python -m json.tool
```

## Data Persistence

SurrealDB database is stored in a Docker named volume (`decisionmemory-data`). Data survives container restarts and rebuilds. For production, consider migrating to PostgreSQL.

## TLS Certificates

Caddy automatically obtains and renews Let's Encrypt certificates for `mcp.mnemox.ai`. No manual certificate management needed.
