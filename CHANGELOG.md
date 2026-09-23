# Changelog

## [0.1.0] - 2024

### Added

- **Synthetic data generation**: Faker-based generation of realistic Canadian care-services data including 300 clients, 110 workers, 6 funders, 7,500+ service visits, 7,257 claims, and 300 reconciliation exceptions.
- **Data quality validation**: 53 reusable validation checks with audit logging. Invalid records are separated and logged, never silently deleted.
- **ETL pipeline**: Python transformation pipeline producing cleaned, validated CSV files from raw synthetic data.
- **PostgreSQL-ready star schema**: Dimensional model with 5 dimensions (`dim_date`, `dim_client`, `dim_worker`, `dim_funder`, `dim_service`) and 4 fact tables (`fact_service_visit`, `fact_claim`, `fact_reconciliation_exception`, `fact_funding_allocation`).
- **SQL analysis**: 8 analysis queries and 8 dashboard-ready analytics views.
- **CSV-first Streamlit dashboard**: Four interactive pages (Executive Overview, Funding Health, Operations, Exceptions and Risk) using processed CSV data with no database requirement.
- **Interpretable claim-review risk model**: Logistic Regression pipeline with StandardScaler and OneHotEncoder preprocessing, train/test split, class weighting, and risk bands (Low/Medium/High).
- **Automated testing**: 46 pytest tests covering data quality, transformation, analytics metrics, risk model, and data access.
- **GitHub Actions CI**: Automated pipeline, model, and test verification on push and pull requests.
- **Documentation**: Executive summary, model card, dashboard guide, data dictionary, architecture, methodology, demo script, interview talking points, and project roadmap.
- **Reproducible scripts**: `setup_local.sh` and `verify_project.sh` for consistent local development.

### Notes

- All data is synthetic and fictional. No real personal, healthcare, client, employee, or company data is used.
- The risk model is a prioritization aid, not an automated decision engine.
- PostgreSQL/Docker support is optional; the project runs fully in CSV-first mode without a database.
