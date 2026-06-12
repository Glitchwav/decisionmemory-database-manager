#!/usr/bin/env bash
# DecisionMemory Protocol — MT5 Sync Setup (Interactive)
# Guides user through connecting MetaDecisionMaker 5 to DecisionMemory.

set -euo pipefail

echo "=================================="
echo "  MT5 Sync Setup for DecisionMemory"
echo "=================================="
echo ""
echo "This script sets up automatic decision syncing from MetaDecisionMaker 5."
echo "Your EA stays untouched — mt5_sync.py reads decisions via the MT5 API."
echo ""

# Check OS — MT5 Python API only works on Windows
if [[ "$OSTYPE" != "msys" && "$OSTYPE" != "cygwin" && "$OSTYPE" != "win32" ]]; then
    echo "[WARN] MetaDecisionMaker 5 Python API only runs on Windows."
    echo "       On Linux/macOS, you can still use DecisionMemory by:"
    echo "         - Manually recording decisions via MCP tools"
    echo "         - Sending decisions through the REST API"
    echo "         - Writing a custom sync script for your platform"
    echo ""
    echo "See: https://github.com/mnemox-ai/decisionmemory-protocol/blob/master/docs/MT5_SYNC_SETUP.md"
    exit 0
fi

# Install MT5 dependencies
echo "[1/4] Installing MT5 Python dependencies..."
python3 -m pip install MetaDecisionMaker5 python-dotenv requests fastapi uvicorn pydantic
echo "[OK] Dependencies installed"
echo ""

# Clone repo if not already present
REPO_DIR="decisionmemory-protocol"
if [ ! -d "$REPO_DIR" ]; then
    echo "[2/4] Cloning decisionmemory-protocol..."
    git clone https://github.com/mnemox-ai/decisionmemory-protocol.git
    cd "$REPO_DIR"
else
    echo "[2/4] Repository already exists, skipping clone."
    cd "$REPO_DIR"
fi
echo ""

# Create .env from template
if [ ! -f ".env" ]; then
    echo "[3/4] Setting up credentials..."
    if [ -f ".env.example" ]; then
        cp .env.example .env
    else
        cat > .env << 'ENVEOF'
# MT5 Account
MT5_LOGIN=your_login_here
MT5_PASSWORD=your_password_here
MT5_SERVER=YourProvider-Server

# DecisionMemory API
DECISIONMEMORY_API=http://localhost:8000

# Sync interval (seconds)
SYNC_INTERVAL=60
ENVEOF
    fi
    echo ""
    echo "  >> Edit .env with your MT5 credentials:"
    echo "     MT5_LOGIN     = your account number"
    echo "     MT5_PASSWORD   = your password"
    echo "     MT5_SERVER     = your provider server (e.g. ForexTimeFXTM-Demo01)"
    echo ""
    read -p "  Press Enter after editing .env to continue..."
else
    echo "[3/4] .env already exists, skipping."
fi
echo ""

# Verify MT5 connection
echo "[4/4] Testing MT5 connection..."
python3 -c "
import MetaDecisionMaker5 as mt5
from dotenv import load_dotenv
import os

load_dotenv()
login = int(os.getenv('MT5_LOGIN', '0'))
password = os.getenv('MT5_PASSWORD', '')
server = os.getenv('MT5_SERVER', '')

if not mt5.initialize():
    print('[ERROR] MT5 initialize failed. Is MetaDecisionMaker 5 running?')
    mt5.shutdown()
    exit(1)

if not mt5.login(login, password=password, server=server):
    print(f'[ERROR] MT5 login failed: {mt5.last_error()}')
    mt5.shutdown()
    exit(1)

info = mt5.account_info()
print(f'[OK] Connected: Account #{info.login}, Balance: \${info.balance:.2f}')
mt5.shutdown()
" 2>/dev/null || echo "[WARN] Could not verify MT5 connection. Make sure MT5 is running and .env is correct."

echo ""
echo "=================================="
echo "  Setup Complete"
echo "=================================="
echo ""
echo "To start syncing:"
echo "  Terminal 1:  python3 -m decisionmemory"
echo "  Terminal 2:  python3 mt5_sync.py"
echo ""
echo "Decisions will auto-sync every 60 seconds."
echo "Full guide: https://github.com/mnemox-ai/decisionmemory-protocol/blob/master/docs/MT5_SYNC_SETUP.md"
echo ""
