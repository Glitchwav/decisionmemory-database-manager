#!/usr/bin/env bash
# DecisionMemory Protocol — Install Script
# Installs decisionmemory-protocol and all dependencies.

set -euo pipefail

echo "=================================="
echo "  DecisionMemory Protocol Installer"
echo "=================================="
echo ""

# Check Python
if ! command -v python3 &>/dev/null; then
    echo "[ERROR] python3 not found. Install Python 3.10+ first."
    echo "        https://www.python.org/downloads/"
    exit 1
fi

PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "[OK] Python ${PYTHON_VERSION} found"

# Check pip
if ! python3 -m pip --version &>/dev/null; then
    echo "[ERROR] pip not found. Install pip first."
    exit 1
fi
echo "[OK] pip available"

# Install decisionmemory-protocol from PyPI
echo ""
echo "Installing decisionmemory-protocol..."
python3 -m pip install --upgrade decisionmemory-protocol

# Verify installation
echo ""
python3 -c "import decisionmemory; print('[OK] decisionmemory-protocol installed successfully')"

echo ""
echo "=================================="
echo "  Installation Complete"
echo "=================================="
echo ""
echo "Next steps:"
echo "  1. Run the demo:  python3 demo.py"
echo "  2. For MT5 sync:  bash .skills/decisionmemory/scripts/setup_mt5.sh"
echo "  3. Start server:  python3 -m decisionmemory"
echo ""
