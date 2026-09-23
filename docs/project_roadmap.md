# Project Roadmap

## Implemented Now

The following features are fully implemented and working:

- **Synthetic data generation**: 7 datasets with Canadian context, intentional anomalies, and deterministic random seed
- **Data quality validation**: 53 reusable checks with audit logging and rejected-record preservation
- **ETL pipeline**: Python transformation producing validated CSV files
- **PostgreSQL-ready star schema**: DDL with dimensions, facts, indexes, and foreign keys
- **SQL analysis**: 8 query-based analyses and 8 dashboard views
- **CSV-first Streamlit dashboard**: 4 interactive pages with Plotly charts and sidebar filters
- **Interpretable claim-review risk model**: Logistic Regression Pipeline with proper preprocessing
- **Automated testing**: 46 pytest tests covering all modules
- **GitHub Actions CI**: Automated pipeline, model, and test verification
- **Documentation**: Executive summary, model card, dashboard guide, data dictionary, architecture, methodology, demo script, interview talking points, project roadmap
- **Reproducible scripts**: `setup_local.sh` and `verify_project.sh`

## Future Enhancements

The following are clearly labeled as future work and are **not** currently implemented:

### Data Warehouse and Cloud Deployment
- Migration to BigQuery, Snowflake, or Redshift for scalable analytics
- Secure deployment with role-based access control
- Cloud infrastructure provisioning and monitoring

### Transformation Testing and Documentation
- dbt models for transformation testing and documentation
- Data contracts and schema validation at the warehouse layer
- Automated data quality monitoring in the warehouse

### Orchestration
- Prefect or Airflow for pipeline orchestration
- Scheduled data refreshes and dependency management
- Alerting on pipeline failures

### Security and Compliance
- Row-level security for multi-tenant data access
- Encryption at rest and in transit
- Audit logging for all data access and model decisions
- Compliance review for healthcare data handling

### Monitoring and Observability
- Data observability with Great Expectations or similar
- Pipeline health monitoring and alerting
- Model drift detection and calibration
- Performance metrics tracking over time

### Model Improvements
- Feedback loops from analyst reviews to model retraining
- Model calibration to improve probability estimates
- Feature importance analysis and explanation reports
- A/B testing of risk-score thresholds

### Client Discovery and Validation
- Real-client discovery sessions to validate metrics
- Stakeholder interviews to refine dashboard questions
- Pilot deployment with actual (anonymized) data
- Iterative refinement based on user feedback

## Important Note

No future enhancement described on this page should be interpreted as already built, tested, or deployed. The project currently operates in CSV-first mode with synthetic data and no cloud deployment.
