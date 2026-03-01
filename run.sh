#!/bin/bash
# Texas Vanity Plate Checker - Setup & Run
# Creates a virtual environment, installs dependencies, and runs the checker.

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_DIR="$SCRIPT_DIR/.venv"

# Create venv if it doesn't exist
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
fi

# Activate venv
source "$VENV_DIR/bin/activate"

# Install dependencies if needed
if ! python3 -c "import playwright" 2>/dev/null; then
    echo "Installing playwright..."
    pip install playwright
    echo "Installing Chromium browser..."
    playwright install chromium
fi

# Run the checker, forwarding all arguments
python3 "$SCRIPT_DIR/plate_checker.py" "$@"
