# Dashboard Guide

## Setup and Run Commands

### Prerequisites

```bash
# Install dependencies
pip install -r requirements.txt

# Generate data and run pipeline
python -m src.pipeline

# Generate risk scores
python -m src.risk_model

# Launch dashboard
streamlit run app/Home.py
```

### Data Source

The dashboard loads from **validated processed CSV files** in `data/processed/`. The pipeline generates these files. Optional PostgreSQL support is available but not required.

### CSV-First Architecture

All dashboard functionality works with processed CSV files. The `app/data_access.py` module loads data from `data/processed/` using `load_processed_data()`. If PostgreSQL is available, it can be configured via environment variables in `.env`, but it is not required.

---

## Dashboard Pages

### 1. Executive Overview (`app/pages/1_Executive_Overview.py`)

**Question**: Where is leadership attention needed first?

- KPI cards for total visits, completed hours, claim dollars, approval rate, open exceptions, and funding-at-risk count
- Monthly trend charts for service volume, claim dollars, approval rate, and exceptions
- Key observations section using actual filtered data

**Sidebar filters**: Date range, city, service program, funder

### 2. Funding Health (`app/pages/2_Funding_Health.py`)

**Question**: Which allocations are approaching budget limits?

- Allocation vs approved spend by funder
- Funding utilization by funder
- Sortable client-funder allocation table with risk flags
- Highlighted allocations at/above 90% utilization

**Decision supported**: Prioritize proactive funding review and prevent service disruption or unapproved spend.

### 3. Operations (`app/pages/3_Operations.py`)

**Question**: Where are staffing and documentation bottlenecks?

- Weekly worker capacity utilization
- Workers exceeding weekly capacity
- Documentation delay trends by month
- Documentation delays by city and service type
- Visit status breakdown

**Decision supported**: Target staffing and documentation-process interventions before they affect claims and client service.

### 4. Exceptions and Risk (`app/pages/4_Exceptions_and_Risk.py`)

**Question**: Which claims and exceptions should analysts review first?

- Exception KPIs (open count, exposure, high-priority open)
- Exception aging by priority and type
- Claim rejection rate by funder and reason
- Duplicate claim candidates and dollar exposure
- Risk-scored claims table with score, band, and reason summary
- Risk-band distribution visualization

**Decision supported**: Triage the highest-value and highest-risk claims and exceptions for analyst review.

---

## Taking Screenshots

1. Run the dashboard: `streamlit run app/Home.py`
2. Navigate to each page
3. Open browser developer tools or use your OS screenshot tool
4. Save screenshots to `dashboard/screenshots/`
5. Name files descriptively: `executive_overview.png`, `funding_health.png`, etc.

**Note**: Screenshots must be captured from actual dashboard runs. Do not create fabricated screenshots.

---

## Troubleshooting

### Missing Processed Data

**Error**: `FileNotFoundError: Missing processed data files`

**Fix**: Run `python -m src.pipeline` to regenerate all data files.

### Missing Model Output

**Error**: Risk scores not appearing on the Exceptions page.

**Fix**: Run `python -m src.risk_model` to generate risk scores. The model requires at least 10 records with both positive and negative classes.

### Missing Dependencies

**Error**: `ModuleNotFoundError` for `streamlit`, `plotly`, or `sklearn`.

**Fix**: Run `pip install -r requirements.txt`.

### Port Already in Use

**Error**: Streamlit fails to start due to port conflict.

**Fix**: Run `streamlit run app/Home.py --server.port 8502` or kill the conflicting process.

### Streamlit Errors

**Common issues**:
- Ensure `PYTHONPATH` includes the project root when running Streamlit
- Check that `app/data_access.py` can find `data/processed/` directory
- Verify all processed CSV files exist

---

## Synthetic-Data Disclaimer

**All data in this application is entirely synthetic and fictional.** No real personal, healthcare, client, employee, or company data is used. This application is intended for portfolio demonstration and analytics education purposes only.

The risk-scoring feature is a synthetic-data prioritization aid. It does not automatically approve, deny, or determine care decisions.
