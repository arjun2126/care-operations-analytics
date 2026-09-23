#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"

echo "=== Care Operations Analytics - Project Verification ==="
echo ""

# Determine Python interpreter
if [ -f ".venv/bin/python" ]; then
    PYTHON=".venv/bin/python"
    echo "Using .venv/bin/python"
elif command -v python3 &>/dev/null; then
    PYTHON="python3"
    echo "Using python3"
else
    echo "ERROR: python3 not found. Please install Python 3.9+ or create a virtual environment."
    echo "Run: ./scripts/setup_local.sh"
    exit 1
fi

# Step 1: Python compilation check
echo "--- Step 1: Python compilation check ---"
$PYTHON -m py_compile src/*.py app/*.py app/pages/*.py
echo "PASS: All Python files compile successfully."

# Step 2: Import validation
echo "--- Step 2: Import validation ---"
$PYTHON -c "import sys; sys.path.insert(0, 'src'); import config; import generate_data; import quality_checks; import transform; import pipeline; import analytics_metrics; import feature_engineering; import risk_model; print('PASS: All src modules import successfully.')"
$PYTHON -c "import sys; sys.path.insert(0, '.'); from app.data_access import load_processed_data; from app.components import *; from app.Home import page; print('PASS: All app modules import successfully.')"

# Step 3: Run pipeline
echo "--- Step 3: Running pipeline ---"
PYTHONPATH=src $PYTHON -m src.pipeline
echo "PASS: Pipeline completed."

# Step 4: Run risk model
echo "--- Step 4: Running risk model ---"
PYTHONPATH=src $PYTHON -m src.risk_model
echo "PASS: Risk model completed."

# Step 5: Run tests
echo "--- Step 5: Running tests ---"
PYTHONPATH=src $PYTHON -m pytest tests/ -q
echo "PASS: All tests passed."

echo ""
echo "=== Verification Complete ==="
echo ""
echo "Project is ready. To launch the dashboard:"
echo "  python -m streamlit run app/Home.py"
