# Interview Talking Points

## 30-Second Project Summary

"I built an end-to-end analytics platform for a fictional Canadian care-services provider. It generates synthetic data, validates it through 53 quality checks, transforms it into a clean pipeline, and serves it through a four-page Streamlit dashboard plus an interpretable risk-scoring model. All data is fictional and generated with Faker. The project runs entirely on CSV files — no database is required to see it work."

## 90-Second Technical Walkthrough

"Starting with the data, I generated seven synthetic datasets covering 300 clients, 110 workers, 6 funders, and over 7,500 service visits across 12 months. I intentionally injected invalid records to test data quality.

For data quality, I built reusable validation functions that check required columns, null values, ID uniqueness, date parsing, non-negative constraints, foreign key integrity, and duplicate detection. Invalid records are preserved in rejected files with full audit trails — they're never silently deleted.

The dimensional model uses a star schema with five dimensions and four fact tables. I chose star schema over normalization because it produces simpler queries, better reporting performance, and is more intuitive for dashboard consumers.

The dashboard is CSV-first — it loads from processed CSV files and works without PostgreSQL. Each page answers a specific business question with interactive Plotly charts and sidebar filters.

For the risk model, I built a Logistic Regression pipeline with a ColumnTransformer that scales numeric features and one-hot encodes categorical features. The train/test split happens before any preprocessing to prevent data leakage. The model categorizes claims into Low, Medium, and High risk bands to help analysts prioritize review."

## Ten Likely Interviewer Questions

### 1. Why use a star schema?

"Star schema simplifies queries by reducing the number of joins needed. For reporting and dashboard consumption, it's much more intuitive than a normalized model. Dimensions are denormalized for faster reads, and the structure maps naturally to how business users think about data — by entity (client, worker, funder) and by time."

### 2. What data-quality checks did you implement?

"53 reusable checks covering required columns, null values in required fields, ID uniqueness, date parsing, non-negative monetary and hour values, foreign key integrity, duplicate detection, and business rules like completed hours tolerance. Results are logged to a quality report CSV. Invalid records are separated into rejected files with full documentation of what was rejected and why."

### 3. Why CSV-first and optional PostgreSQL?

"CSV-first means the project runs immediately without Docker or PostgreSQL. Anyone can clone the repo, install dependencies, and see the dashboard. PostgreSQL is available as an optional backend for the ETL loading layer via SQLAlchemy, but it's not required. This makes the project accessible to any reviewer without infrastructure setup."

### 4. How does the risk model work?

"It's a Logistic Regression model in a sklearn Pipeline with a ColumnTransformer. Numeric features like claim amount and documentation delay are scaled with StandardScaler. Categorical features like funder type and service type are one-hot encoded with OneHotEncoder. The model uses class_weight='balanced' to handle class imbalance. Risk scores range from 0 to 1 and map to Low, Medium, and High bands."

### 5. What are the model limitations and why is it not an automated decision engine?

"Key limitations: synthetic data limits generalizability, the dataset has a modest number of rejected claims (752 out of 7,257), and the model has modest recall which means it may miss some high-risk claims. The model is a prioritization aid — it tells analysts which claims to review first. It should never be used to automatically approve, deny, or determine care decisions. Healthcare decisions require human oversight, regulatory compliance, and accountability."

### 6. How did you prevent feature leakage?

"Strict rule: no post-decision features. I excluded rejection_reason, exception status, and exception type from features. The target is defined as claim rejected OR duplicate candidate — both of which are known at review time. Features like claim amount, documentation delay, late submission flag, and duplicate candidate flag are all available before a review decision is made. The train/test split happens before any preprocessing fits."

### 7. How would you protect sensitive data for a real client?

"For a real client, I would never use actual patient or client data. I would use synthetic data generation with the same statistical properties as the real data. All data would be anonymized or pseudonymized. Access would be restricted through role-based access controls. The pipeline would run in a secure, air-gapped environment. I would also implement data retention policies and audit logging for all data access."

### 8. How would you scale this into a cloud solution?

"I would move the data warehouse to BigQuery, Snowflake, or Redshift. I would add dbt for transformation testing and documentation. I would use Prefect or Airflow for orchestration. For deployment, I would use secure containerized services with role-based access. Monitoring would track data quality, pipeline health, and model drift. All of these are clearly future enhancements, not current implementation."

### 9. Why did you choose these dashboard pages and metrics?

"The four pages map directly to the four business problems the company identified: funding utilization, claims review, operations, and exceptions. Each page has KPIs that answer the specific question leaders asked. I chose Plotly for interactivity because hiring managers can explore the data themselves. The sidebar filters allow drilling into specific cities, funders, or date ranges."

### 10. What would you build next?

"Several future enhancements: warehouse/cloud deployment to BigQuery or Snowflake, dbt for transformation testing and documentation, orchestration with Prefect or Airflow, secure deployment with role-based access, data observability and monitoring, model calibration and feedback loops, and real-client discovery to validate metrics against actual business data. All of these are clearly labeled as future work in the project roadmap."

## How I Would Describe the Model Results

"The model uses Logistic Regression with class_weight='balanced' and achieved a precision of approximately 63%, recall of approximately 30%, and F1 score of approximately 41% with an ROC-AUC of approximately 0.68 on the hold-out test set.

I want to be transparent about these results. The recall is modest, which means the model identifies a limited proportion of actual high-risk claims. This is expected with synthetic data and a balanced model — we're prioritizing interpretability over raw performance. The model is not production-ready for real client decisions. It serves as a portfolio demonstration of how to build an interpretable risk-prioritization pipeline with proper train/test splitting, preprocessing pipelines, and leakage prevention."
