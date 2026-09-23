# Contributing

## Setup

1. Clone the repository.
2. Run the setup script: `bash scripts/setup_local.sh`
3. Or manually create a virtual environment and install dependencies.

## Virtual Environment

This project uses Python virtual environments to isolate dependencies.

**macOS/Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

**Windows:**
```bash
py -m venv .venv
.venv\Scripts\activate
py -m pip install -r requirements.txt
```

## Running the Pipeline

Generate synthetic data and run the ETL pipeline:
```bash
python -m src.pipeline
```

## Training the Risk Model

Generate claim-review risk scores:
```bash
python -m src.risk_model
```

## Running Tests

Run all tests:
```bash
pytest tests/ -v
```

Run specific tests:
```bash
pytest tests/test_risk_model.py -v
pytest tests/test_analytics_metrics.py -v
```

## Local Verification

Run the full verification script:
```bash
bash scripts/verify_project.sh
```

## Synthetic Data Policy

All data in this project is synthetic and fictional. No real personal, healthcare, client, employee, or company data is used. Do not replace synthetic data with real client data without proper authorization and privacy review.

## Branch and Commit Conventions

- Use descriptive branch names: `feature/dashboard-polish`, `fix/risk-model`, `docs/readme-update`
- Commit messages should describe the change clearly
- Use conventional format: `feat:`, `fix:`, `docs:`, `test:`, `refactor:`

## Pull Requests

1. Ensure all tests pass locally.
2. Update documentation if changing functionality.
3. Do not include generated CSV files or model artifacts in commits.
4. Verify `.gitignore` properly excludes generated files.
