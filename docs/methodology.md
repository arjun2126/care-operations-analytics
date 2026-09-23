# Methodology

## Synthetic Data Assumptions

All data in this project is synthetic and generated using the Faker library configured for Canadian locale. The following assumptions guide data generation:

### Client Population
- 300 clients across 25 Canadian cities, weighted toward Ontario
- Service programs reflect typical Canadian home care categories
- Active/inactive ratio approximately 70/30, reflecting real-world attrition

### Worker Population
- 110 workers across 7 healthcare professional types
- Weekly capacity ranges from 20-60 hours, reflecting part-time and full-time roles
- Hire dates spanning the last 10 years

### Funding
- 6 funders with provincial, federal, municipal, and private funding types
- Claim limits range from $500K to $5M per funder
- Documentation SLA ranges from 7-30 days

### Service Visits
- 7,500 visits across 12 months (Jan-Dec 2024)
- ~80% completion rate, ~10% cancelled, ~10% missed
- Documentation delays range from -1 to 14 days

### Claims
- All completed visits generate a claim
- ~60% approved, ~8% rejected, ~32% pending review
- ~15% submitted late, ~5% flagged as duplicate candidates

### Reconciliation Exceptions
- 300 exceptions from a sample of claims
- ~35% remain unresolved (for aging analysis)
- Priority distribution: 20% High, 50% Medium, 30% Low

---

## Data-Quality Handling

### Philosophy
Data quality is treated as a first-class concern, not an afterthought. The system is designed to:

1. **Detect** problems through configurable, reusable rules
2. **Report** issues transparently via the quality report
3. **Separate** valid from invalid records without silent deletion
4. **Log** what was rejected and why

### Check Categories

| Category | Description | Action |
|----------|-------------|--------|
| Column validation | Required columns present | FAIL if missing |
| Null detection | Required fields populated | WARN on nulls |
| Uniqueness | No duplicate IDs | FAIL on duplicates |
| Date parsing | Dates are valid | WARN on unparseable |
| Non-negative | Amounts/hours >= 0 | WARN on negatives |
| FK integrity | References valid | FAIL on invalid |
| Business rules | Hours within tolerance | WARN on violation |

### Handling Strategy
- Invalid records are written to `*_rejected.csv` files
- Valid records are loaded into the star schema
- Quality report is written to `data/processed/quality_report.csv`
- Loading summary tracks valid and rejected counts per table

---

## Why a Star Schema Was Selected

The star schema was chosen over normalized models for the following reasons:

1. **Query simplicity**: Dashboard consumers need straightforward joins, not complex multi-table normalization
2. **Performance**: Fewer joins mean faster query execution for reporting workloads
3. **Intuitive navigation**: Business users can understand the relationship between dimensions and facts
4. **Flexibility**: New dimensions can be added without restructuring existing facts
5. **Industry standard**: Star schema is the most widely understood dimensional model for analytics

The design includes a conformed `dim_service` dimension to enable cross-fact analysis of service types without duplicating service metadata across fact tables.

### Dimension Selection Rationale

- **dim_date**: Essential for all time-based analysis; avoids date function overhead in queries
- **dim_client**: Enables client-level segmentation and analysis
- **dim_worker**: Supports capacity planning and worker performance analysis
- **dim_funder**: Central to funding utilization and claims analysis
- **dim_service**: Conformed dimension for service type standardization

### Fact Table Granularity

- **fact_service_visit**: One row per visit (atomic)
- **fact_claim**: One row per claim (atomic)
- **fact_reconciliation_exception**: One row per exception (atomic)
- **fact_funding_allocation**: One row per client-funder allocation

---

## Known Limitations

1. **Synthetic data**: All data is fictional and does not represent any real organization or individual. Analytical insights are illustrative only.

2. **Fixed date range**: Data spans only 2024. Multi-year trend analysis is not possible.

3. **Single-year capacity**: Worker capacity is annual; seasonal variation within months is not modeled.

4. **No real-time streaming**: The pipeline is batch-oriented and not designed for real-time analytics.

5. **Database dependency**: Full ETL requires PostgreSQL running via Docker. Data generation and quality checks work without a database.

6. **Sample-size constraints**: With 300 clients and 6 funders, some client-funder combinations may have limited data, affecting statistical significance of certain analyses.

7. **No historical dimension**: The star schema does not track changes over time (SCD Type 2). Client, worker, and funder attributes reflect their current state as of data generation.

8. **Documentation delay calculation**: Delay days are generated independently of actual SLA calculation. In a production system, delay would be calculated as `claim_date - service_date - documentation_sla_days`.

9. **Exception resolution**: The 35% unresolved rate is fixed for portfolio demonstration. Real-world resolution rates vary significantly by exception type.

10. **Geographic limitations**: Cities are limited to 25 Canadian locations. A production system would include all relevant service areas.

---

## Testing Approach

Tests verify:
- Data-quality rules detect expected issues
- Transformation functions correctly filter invalid records
- Foreign key validation catches invalid references
- Duplicate detection works as expected
- Cleaning produces the expected number of valid/invalid records

All tests run without requiring a live database using pytest.
