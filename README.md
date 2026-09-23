# Care Operations Analytics Command Center

**An end-to-end analytics solution for a fictional Canadian care-services provider that identifies funding risk, claim-review priorities, operational bottlenecks, and unresolved reconciliation exceptions.**

> **All records are fictional and generated solely for portfolio demonstration. No real personal, healthcare, client, employee, or company data is used.**

---

## Screenshots

The following screenshots show the working local Streamlit dashboard:

![Home dashboard](dashboard/screenshots/home.jpg)
![Executive Overview dashboard](dashboard/screenshots/executive-overview.jpg)
![Funding Health dashboard](dashboard/screenshots/funding-health.jpg)
![Operations dashboard](dashboard/screenshots/operations.jpg)
![Exceptions and Risk dashboard](dashboard/screenshots/exceptions-risk.jpg)

---

## Business Problem

A fictional Canadian care-services provider delivers in-home services funded by multiple funders. Leaders lacked visibility into:

- **Funding utilization** and possible budget overruns
- **Claims** likely to be rejected or need manual review
- **Operational risks** such as late documentation and worker-capacity constraints
- **Aging reconciliation exceptions** requiring resolution

---

## Key Capabilities

- Synthetic-data generation with Canadian locale
- Data-quality validation with 53 checks and audit logging
- Python ETL/transformation pipeline
- PostgreSQL-ready star schema and SQL analysis
- CSV-first Streamlit dashboard (no database required)
- Funding, operations, and exceptions analysis
- Interpretable claim-review risk prioritization
- Consulting-style executive recommendations
- Automated test coverage and CI configuration

---

## Architecture

```mermaid
graph TD
    A[Python Faker] -->|Generate| B(Raw CSV Files)
    B --> C{Data Quality Checks}
    C -->|Pass| D[Cleaned CSV Files]
    C -->|Fail| E[Rejected Records Log]
    D --> F[PostgreSQL Star Schema]
    D --> G[Streamlit Dashboard]
    D --> H[Risk Model]
    G --> I[Executive Overview]
    G --> J[Funding Health]
    G --> K[Operations]
    G --> L[Exceptions & Risk]
    H --> M[Risk Scores]
```

Full architecture explanation: [docs/architecture.md](docs/architecture.md)

---

## Results at a Glance

| Metric | Value |
|--------|-------|
| Total clients | 300 |
| Total workers | 110 |
| Total funders | 6 |
| Service visits | 7,500+ |
| Claims | 7,257 |
| Reconciliation exceptions | 300 |

**Risk model evaluation** (test set):

| Metric | Value |
|--------|-------|
| Precision | 0.632 |
| Recall | 0.299 |
| F1 Score | 0.406 |
| ROC-AUC | 0.675 |

The model is a **prioritization aid** — it identifies which claims to review first. It is not an automated decision system and must not be used to approve, deny, or determine care decisions.

---

## Technology Stack

Python, pandas, scikit-learn, Streamlit, Plotly, PostgreSQL, Docker Compose, pytest, GitHub Actions

---

## Quick Start

### macOS / Linux

```bash
# 1. Create virtual environment and install dependencies
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 2. Generate data and run pipeline
python -m src.pipeline

# 3. Generate risk scores
python -m src.risk_model

# 4. Launch dashboard
python -m streamlit run app/Home.py

# 5. Run tests
pytest tests/ -v
```

### Windows

```bash
py -m venv .venv
.venv\Scripts\activate
py -m pip install -r requirements.txt
py -m src.pipeline
py -m src.risk_model
py -m streamlit run app/Home.py
```

**No PostgreSQL/Docker required.** The project runs entirely on processed CSV files.

---

## Optional PostgreSQL/Docker Setup

PostgreSQL is optional and clearly labelled as such. CSV-first mode makes the project immediately runnable.

```bash
docker compose up -d
make init
```

To verify the database is running:
```bash
docker compose ps
```

---

## Dashboard Walkthrough

| Page | Question Answered | Decision Supported |
|------|-------------------|--------------------|
| **Executive Overview** | Where is leadership attention needed first? | Identify priority areas for leadership |
| **Funding Health** | Which allocations are approaching budget limits? | Prioritize proactive funding review |
| **Operations** | Where are staffing and documentation bottlenecks? | Target staffing and documentation interventions |
| **Exceptions & Risk** | Which claims and exceptions should analysts review first? | Triage highest-value and highest-risk claims |

---

## Project Structure

```
care-operations-analytics/
├── app/                       # Streamlit dashboard
│   ├── Home.py                # Dashboard home page
│   ├── components.py          # Reusable formatting helpers
│   ├── data_access.py         # CSV-first data loading
│   └── pages/                 # Dashboard pages
├── data/                      # Generated data (Git ignored)
│   ├── raw/
│   └── processed/
├── docs/                      # Documentation
│   ├── executive_summary.md
│   ├── model_card.md
│   ├── dashboard_guide.md
│   ├── data_dictionary.md
│   ├── architecture.md
│   ├── methodology.md
│   ├── demo_script.md
│   ├── interview_talking_points.md
│   └── project_roadmap.md
├── scripts/                   # Local setup and verification
├── src/                       # Python source modules
├── tests/                     # Pytest tests
├── dashboard/                 # Screenshots
├── sql/                       # Star schema DDL and queries
├── requirements.txt           # Python dependencies
├── .github/workflows/ci.yml   # GitHub Actions CI
├── README.md                  # This file
├── LICENSE                    # MIT License
├── CONTRIBUTING.md            # Contribution guide
└── CHANGELOG.md               # Version history
```

---

## Testing and CI

- **Local test command**: `pytest tests/ -v`
- **Local verification**: `bash scripts/verify_project.sh`
- **CI**: GitHub Actions runs the CSV-first pipeline, model, and tests on push and pull requests
- **No Docker in CI**: CI uses lightweight verification that does not require PostgreSQL

---

## Documentation

- [Executive Summary](docs/executive_summary.md) — Evidence-based consulting findings
- [Model Card](docs/model_card.md) — Risk model purpose, features, limitations
- [Dashboard Guide](docs/dashboard_guide.md) — Setup, pages, troubleshooting
- [Data Dictionary](docs/data_dictionary.md) — All fields and relationships
- [Architecture](docs/architecture.md) — System design and Mermaid diagram
- [Methodology](docs/methodology.md) — Assumptions and known limitations
- [Demo Script](docs/demo_script.md) — 2-minute walkthrough script
- [Interview Talking Points](docs/interview_talking_points.md) — Common questions and answers
- [Project Roadmap](docs/project_roadmap.md) — Implemented vs future features

---

## Future Enhancements

These are clearly future work and are **not** currently implemented:

- BigQuery, Snowflake, or Redshift warehouse migration
- dbt tests and documentation
- Orchestration with Prefect or Airflow
- Secure deployment and role-based access
- Data observability and monitoring
- Model calibration and feedback loops
- Real-client discovery and metric validation

See [docs/project_roadmap.md](docs/project_roadmap.md) for details.

---

## Data Disclaimer

**All data in this project is entirely synthetic and fictional.** No real personal, healthcare, client, employee, or company data is used or generated. All names, cities, and identifiers are fictional creations using the Faker library configured for Canadian locale. This project is intended for portfolio demonstration and analytics education purposes only.

The claim risk model is a synthetic-data prioritization aid. It does not automatically approve, deny, or determine care decisions. Model metrics are modest and reflect the limitations of synthetic data.
