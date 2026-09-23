# Care Operations Analytics

**End-to-end analytics solution for Canadian care-services funding visibility, claims integrity, and operational efficiency.**

---

## Business Problem

A fictional Canadian care-services provider delivers in-home services funded by multiple funders. Leaders lack visibility into:

1. **Funding utilization** and possible budget overruns
2. **Claims** that may be rejected or need manual review
3. **Operational problems** such as late documentation and worker-capacity constraints
4. **Aging reconciliation exceptions** requiring resolution

This project provides a complete analytics foundation to address these gaps through synthetic data generation, data-quality validation, dimensional modeling, and production-style SQL analysis.

---

## Architecture Overview

The solution follows a classic analytics pipeline:

```
Raw Synthetic Data → Data Quality Validation → Transformation/Cleaning → PostgreSQL Star Schema → Analytics Views → Dashboard Layer
```

1. **Generate** synthetic datasets using Faker with Canadian context
2. **Validate** data quality with reusable, configurable checks
3. **Clean** records, separating valid from invalid with full audit logging
4. **Load** into PostgreSQL star schema (dimensions + facts)
5. **Analyze** with production SQL views and queries
6. **Visualize** via dashboard-ready views

---

## Tech Stack

- **Python 3.11+** — Core application logic
- **pandas** — Data manipulation and transformation
- **Faker** — Synthetic data generation
- **SQLAlchemy** — Database connection and loading
- **psycopg** — PostgreSQL adapter
- **PostgreSQL** — Analytics data warehouse
- **Docker Compose** — Database environment
- **pytest** — Automated testing
- **Streamlit** — Interactive dashboard
- **Plotly** — Interactive visualizations
- **scikit-learn** — Claim risk scoring
- **joblib** — Model persistence
- **python-dotenv** — Environment configuration

---

## Repository Layout

```
care-operations-analytics/
├── README.md                  # This file
├── requirements.txt           # Python dependencies
├── .gitignore                 # Git ignore rules
├── .env.example               # Environment template
├── docker-compose.yml         # PostgreSQL container
├── Makefile                   # Command shortcuts
├── app/                       # Streamlit dashboard
│   ├── __init__.py
│   ├── Home.py                # Dashboard home page
│   ├── components.py          # Reusable formatting helpers
│   ├── data_access.py         # CSV-first data loading layer
│   └── pages/
│       ├── 1_Executive_Overview.py
│       ├── 2_Funding_Health.py
│       ├── 3_Operations.py
│       └── 4_Exceptions_and_Risk.py
├── data/
│   ├── raw/                   # Generated synthetic CSV files
│   └── processed/             # Cleaned data + quality reports + model outputs
├── docs/
│   ├── data_dictionary.md     # Field-level documentation
│   ├── architecture.md        # Architecture diagram & explanation
│   ├── methodology.md         # Methodology and assumptions
│   ├── executive_summary.md   # Consulting-style findings
│   ├── dashboard_guide.md     # Dashboard setup and usage
│   └── model_card.md          # Risk model documentation
├── notebooks/                 # Jupyter notebooks
│   └── analysis_walkthrough.ipynb
├── sql/
│   ├── 01_create_schema.sql   # Star schema DDL
│   ├── 02_analytics_views.sql # Dashboard views
│   └── 03_analysis_queries.sql# Production analysis queries
├── src/
│   ├── __init__.py
│   ├── config.py              # Centralized configuration
│   ├── generate_data.py       # Synthetic data generation
│   ├── quality_checks.py      # Reusable data-quality rules
│   ├── transform.py           # Cleaning and validation
│   ├── load_data.py           # PostgreSQL ETL loading (optional)
│   ├── pipeline.py            # Single entry point
│   ├── analytics_metrics.py   # Dashboard metric calculations
│   ├── feature_engineering.py # Risk model feature engineering
│   └── risk_model.py          # Claim-review risk scoring
├── tests/
│   ├── __init__.py
│   ├── test_quality_checks.py
│   ├── test_transform.py
│   ├── test_analytics_metrics.py
│   ├── test_risk_model.py
│   └── test_data_access.py
└── dashboard/                 # Dashboard outputs
    ├── screenshots/           # Dashboard screenshots
    └── .gitkeep
```

---

## Setup Instructions

### 1. Clone the repository

```bash
cd care-operations-analytics
```

### 2. Create virtual environment and install dependencies

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Configure environment

```bash
cp .env.example .env
# Edit .env as needed
```

### 4. Start PostgreSQL (requires Docker)

```bash
docker compose up -d
```

Wait for the database to be ready:
```bash
docker compose exec postgres pg_isready -U care_analyst -d care_analytics
```

### 5. Initialize database schema

```bash
make init
```

Or manually:
```bash
docker compose exec postgres psql -U care_analyst -d care_analytics -f sql/01_create_schema.sql
docker compose exec postgres psql -U care_analyst -d care_analytics -f sql/02_analytics_views.sql
```

### 6. Run the full pipeline

```bash
python -m src.pipeline
```

Or use Make:
```bash
make pipeline
```

### 7. Run SQL analysis queries

```bash
docker compose exec postgres psql -U care_analyst -d care_analytics -f sql/03_analysis_queries.sql
```

### 8. Run tests

```bash
pytest tests/ -v
```

---

## Running Individual Components

| Command | Description |
|---------|-------------|
| `python -m src.generate_data` | Generate raw synthetic data only |
| `python -m src.quality_checks` | Run data quality checks on raw data |
| `python -m src.transform` | Clean and transform data |
| `python -m src.load_data` | Load cleaned data into PostgreSQL |
| `python -m src.pipeline` | Run full ETL pipeline |
| `make test` | Run all pytest tests |
| `make up` | Start PostgreSQL via Docker |
| `make init` | Initialize database schema |

### Dashboard and Risk Model

| Command | Description |
|---------|-------------|
| `streamlit run app/Home.py` | Launch the Streamlit dashboard |
| `python -m src.risk_model` | Train and generate claim risk scores |
| `python -m src.pipeline` | Run full ETL pipeline (generates data + quality checks) |

---

## Dashboard Pages

The Streamlit dashboard (`streamlit run app/Home.py`) provides four interactive pages, all working with processed CSV files (no database required):

| Page | Question Answered |
|------|-------------------|
| **Executive Overview** | Where is leadership attention needed first? |
| **Funding Health** | Which allocations are approaching budget limits? |
| **Operations** | Where are staffing and documentation bottlenecks? |
| **Exceptions & Risk** | Which claims and exceptions should analysts review first? |

The dashboard uses a **CSV-first** architecture. All data loads from `data/processed/` CSV files. Optional PostgreSQL support is available via environment variables in `.env`, but is not required.

---

## Claim-Review Risk Score

The risk model (`python -m src.risk_model`) provides an interpretable claim prioritization system:

- **Model**: Logistic Regression (interpretable, class-weighted)
- **Target**: Claim rejected OR flagged as duplicate candidate
- **Features**: Claim amount, documentation delay, late submission flag, duplicate flag, hours variance, funder type, service type
- **Leakage prevention**: No rejection_reason or exception fields used as features
- **Output**: Risk score (0–1), risk band (Low/Medium/High), human-readable reason summary
- **Metrics**: Precision, recall, F1, ROC-AUC, confusion matrix

**Limitations**: Synthetic data only. This is a prioritization aid, NOT an automated decision engine. It must never be used to approve, deny, or determine care decisions. See `docs/model_card.md` for full details.

---

## Key Documentation

- [Executive Summary](docs/executive_summary.md) — Evidence-based consulting findings
- [Dashboard Guide](docs/dashboard_guide.md) — Setup, pages, troubleshooting
- [Model Card](docs/model_card.md) — Risk model purpose, features, limitations
- [Data Dictionary](docs/data_dictionary.md) — All fields and relationships
- [Architecture](docs/architecture.md) — System design and Mermaid diagram
- [Methodology](docs/methodology.md) — Assumptions and known limitations

---

## Running the Full Stack

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Generate data and run pipeline
python -m src.pipeline

# 3. Generate risk scores
python -m src.risk_model

# 4. Launch dashboard
streamlit run app/Home.py

# 5. Run all tests
pytest tests/ -v
```

**No PostgreSQL/Docker required** for the dashboard and risk model. The pipeline generates processed CSV files that the dashboard consumes directly.

---

## Intentional Anomalies

This dataset includes deliberately generated anomalies for portfolio analytics demonstration:

- **Invalid raw records**: Records with null client IDs, negative hours, and missing dates are intentionally injected to exercise data-quality checks
- **Late documentation**: ~15% of claims have late submission flags
- **Duplicate candidates**: ~5% of claims are flagged as potential duplicates
- **Rejected claims**: ~8% of claims have rejection reasons including missing documentation and funding limits
- **Capacity violations**: Some workers have weekly completed hours exceeding their capacity
- **Unresolved exceptions**: ~35% of reconciliation exceptions remain open for aging analysis

**All anomalies are synthetic and fictional.** No real personal, healthcare, client, employee, or company data is used.

---

## What This Demonstrates for an Analytics Consultant

1. **End-to-end data engineering**: From synthetic data generation through to dashboard-ready analytics views
2. **Data quality as a first-class concern**: Reusable, testable quality rules with full audit trails
3. **Dimensional modeling expertise**: Star schema design with proper FK relationships, indexes, and documentation
4. **SQL analytics proficiency**: Production-style queries addressing real business questions
5. **Python automation**: Clean pipeline architecture with logging, configuration, and idempotent loading
6. **Testing discipline**: Practical pytest coverage for data validation, risk modeling, and data access
7. **Dashboard development**: Professional multi-page Streamlit application with interactive Plotly charts
8. **Risk modeling**: Interpretable logistic regression with proper leakage prevention and model documentation
9. **Consulting communication**: Executive summaries, model cards, and methodology docs
10. **Canadian domain awareness**: Realistic Canadian cities, names, and care-service programs

---

## Data Disclaimer

**All data in this project is entirely synthetic and fictional.** No real personal, healthcare, client, employee, or company data is used or generated. All names, cities, and identifiers are fictional creations using the Faker library configured for Canadian locale. This project is intended for portfolio demonstration and analytics education purposes only.

The claim risk model is a synthetic-data prioritization aid. It does not automatically approve, deny, or determine care decisions.
