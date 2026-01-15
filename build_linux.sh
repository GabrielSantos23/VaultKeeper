#!/bin/bash
# VaultKeeper Build Script for Linux
# Creates a standalone executable for Linux

set -e

echo "=========================================="
echo "  VaultKeeper Build Script - Linux"
echo "=========================================="

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Check Python
echo -e "\n${YELLOW}[1/5] Checking Python...${NC}"
if command -v python3 &> /dev/null; then
    PYTHON=python3
elif command -v python &> /dev/null; then
    PYTHON=python
else
    echo -e "${RED}Error: Python not found!${NC}"
    exit 1
fi
echo "Using: $($PYTHON --version)"

# Create/activate virtual environment
echo -e "\n${YELLOW}[2/5] Setting up virtual environment...${NC}"
if [ ! -d ".venv" ]; then
    $PYTHON -m venv .venv
fi
source .venv/bin/activate

# Install dependencies
echo -e "\n${YELLOW}[3/5] Installing dependencies...${NC}"
pip install --upgrade pip
pip install -r requirements.txt
pip install pyinstaller

# Build
echo -e "\n${YELLOW}[4/5] Building executable...${NC}"
pyinstaller vaultkeeper.spec --clean --noconfirm

# Create distribution package
echo -e "\n${YELLOW}[5/5] Creating distribution package...${NC}"
VERSION=$(grep -oP 'version.*"\K[^"]+' app/__init__.py 2>/dev/null || echo "1.0.0")
DIST_NAME="VaultKeeper-${VERSION}-linux-x64"
DIST_DIR="dist/${DIST_NAME}"

mkdir -p "$DIST_DIR"
cp dist/VaultKeeper "$DIST_DIR/"
cp README.md "$DIST_DIR/" 2>/dev/null || true

# Create tar.gz
cd dist
tar -czvf "${DIST_NAME}.tar.gz" "${DIST_NAME}"
cd ..

echo -e "\n${GREEN}=========================================="
echo "  Build Complete!"
echo "==========================================${NC}"
echo -e "Executable: ${GREEN}dist/VaultKeeper${NC}"
echo -e "Package: ${GREEN}dist/${DIST_NAME}.tar.gz${NC}"
echo ""
echo "To run: ./dist/VaultKeeper"
