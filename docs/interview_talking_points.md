# Interview Talking Points

## 30-Second Project Summary

"I built an analytics project for a fictional Canadian care-services provider. It generates synthetic data, checks it through 53 quality rules, then serves it up in a four-page Streamlit dashboard plus an interpretable risk-scoring model. Everything is generated with Faker, and it all runs off CSV files — no database needed to see it work."

## 90-Second Technical Walkthrough

"On the data side, I generated seven synthetic datasets covering 300 clients, 110 workers, 6 funders, and over 7,500 service visits across 12 months, and I deliberately injected some invalid records to test the quality checks.

The quality layer is a set of reusable validation functions that check required columns, nulls, ID uniqueness, date parsing, non-negative values, foreign keys, and duplicates. Invalid records get written to a rejected file with a reason, so nothing is silently dropped.

The schema is a star, five dimensions and four fact tables. I chose it over normalized tables because it makes the queries shorter and reads naturally for a dashboard.

The dashboard loads processed CSVs, so it works with no database. Each page answers one business question with Plotly charts and sidebar filters.

For the risk model, I used a logistic regression inside a sklearn pipeline — a ColumnTransformer scales the numeric features and one-hot encodes the categorical ones, and the train/test split happens before any preprocessing so there's no leakage. Claims land in Low, Medium, or High bands for review prioritization."

## Ten Likely Interviewer Questions

### 1. Why use a star schema?

"Fewer joins, shorter queries. For reporting, a star schema reads the way a business thinks — you filter by client, worker, funder, or time, and the facts are already laid out for you. Normalized tables are cleaner to store but painful to query repeatedly."

### 2. What data-quality checks did you implement?

"53 reusable checks covering required columns, nulls in required fields, ID uniqueness, date parsing, non-negative money and hours, foreign keys, duplicates, and a couple of business rules like completed-hours tolerance. Results go to a quality report CSV, and invalid records are written to a rejected file with the reason documented."

### 3. Why CSV-first and optional PostgreSQL?

"CSV-first means the repo works the minute you clone it — install dependencies and the dashboard runs, no Docker or database. PostgreSQL is there as an optional ETL target via SQLAlchemy, but nothing on the critical path depends on it."

### 4. How does the risk model work?

"Logistic regression inside a sklearn pipeline. A ColumnTransformer scales the numeric features with StandardScaler and one-hot encodes funder and service type, with class_weight set to 'balanced' because the positive class is small. The output is a score from 0 to 1, bucketed into Low, Medium, and High."

### 5. What are the model limitations and why is it not an automated decision engine?

"A few things. It's trained on synthetic data, so it generalizes to nothing yet. The rejected set is small — roughly 752 out of 7,257 claims — and recall is modest, around 30%, so it misses some genuinely risky claims. It's meant to prioritize, not to decide. Approving or denying claims carries regulatory and human accountability, so the model only ever suggests what an analyst should open next."

### 6. How did you prevent feature leakage?

"Hard rule: no post-decision features. I excluded rejection reason, exception status, and exception type from the model entirely. The target is 'rejected OR flagged as a duplicate candidate,' both known at review time, and every feature — claim amount, documentation delay, late submission, duplicate flag — is available before a decision is made. The train/test split also happens before any preprocessing is fit."

### 7. How would you protect sensitive data for a real client?

"I wouldn't push real patient or client data into a pipeline like this. I'd generate synthetic data that reproduces the same statistical shape, or use anonymized data behind role-based access, in a locked-down environment, with retention policies and audit logging on every read."

### 8. How would you scale this into a cloud solution?

"I'd move the warehouse to BigQuery, Snowflake, or Redshift, add dbt so the transformations are tested and documented, and orchestrate runs with Prefect or Airflow. Deployment would sit behind role-based access with monitoring on data quality and model drift. I want to be clear: none of this is built — it's all future work on the roadmap."

### 9. Why did you choose these dashboard pages and metrics?

"The four pages each map to a question leadership said they couldn't answer — funding use, claims, operations, and exceptions. The KPIs on each page are the numbers you'd want first, and Plotly lets whoever is reviewing click through the charts themselves instead of taking my word for it."

### 10. What would you build next?

"Warehouse migration to BigQuery or Snowflake, dbt tests, Prefect or Airflow orchestration, secure deployment with role-based access, observability and model drift monitoring, and a discovery pass with a real client to validate that the metrics actually match how they run the business. Those are all future ideas — the roadmap marks them as not implemented."

## How I Would Describe the Model Results

"The model is logistic regression with class_weight='balanced'. On the hold-out test set it gets precision around 63%, recall around 30%, an F1 around 41%, and an ROC-AUC around 0.68.

I'd rather be blunt about it than oversell it. Recall at 30% means it catches a limited share of the actually-high-risk claims. That's what you get with synthetic data and a model tuned for interpretability rather than raw accuracy. It is a portfolio demonstration of a clean, leakage-free triage pipeline — not something you'd point at real claims today."
