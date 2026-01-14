#!/bin/bash
# VaultKeeper Native Host Wrapper
# Activates virtual environment and runs the host

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Try different venv locations
if [ -f "$PROJECT_DIR/.venv/bin/python" ]; then
    exec "$PROJECT_DIR/.venv/bin/python" "$SCRIPT_DIR/host.py"
elif [ -f "$PROJECT_DIR/venv/bin/python" ]; then
    exec "$PROJECT_DIR/venv/bin/python" "$SCRIPT_DIR/host.py"
else
    # Fallback: system Python
    exec python3 "$SCRIPT_DIR/host.py"
fi
