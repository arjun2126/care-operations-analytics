#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"

echo "=== Care Operations Analytics - Local Setup ==="
echo "Repository root: $REPO_ROOT"
echo ""

# Check for Python 3
if ! command -v python3 &>/dev/null; then
    echo "ERROR: python3 is not installed. Please install Python 3.9+ and try again."
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
else
    echo "Virtual environment already exists. Skipping creation."
fi

# Activate virtual environment
source .venv/bin/activate
echo "Virtual environment activated."

# Upgrade pip
echo "Upgrading pip..."
python -m pip install --upgrade pip -q

# Install requirements
echo "Installing dependencies..."
python -m pip install -r requirements.txt -q

# Copy .env.example to .env if .env doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env from .env.example..."
    cp .env.example .env
    echo ""
    echo "NOTE: .env is for local development only. It contains placeholder values."
    echo "      Do not commit .env to version control."
else
    echo ".env already exists. Skipping."
fi

echo ""
echo "=== Setup Complete ==="
echo ""
echo "Next steps:"
echo "  python -m src.pipeline"
echo "  python -m src.risk_model"
echo "  python -m streamlit run app/Home.py"
echo ""
echo "To activate the virtual environment manually:"
echo "  source .venv/bin/activate"
