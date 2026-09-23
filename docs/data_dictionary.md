# Data Dictionary

## Overview

This document defines every dataset (raw CSV) and database table (star schema), including all fields, data types, keys, and relationships.

---

## Raw Source Datasets

### 1. clients.csv

| Field | Type | Description |
|-------|------|-------------|
| `client_id` | VARCHAR(10) | Unique client identifier (PK) |
| `client_name` | VARCHAR(255) | Full name of the client |
| `city` | VARCHAR(100) | Canadian city where client resides |
| `service_program` | VARCHAR(100) | Type of care service program |
| `intake_date` | DATE | Date client was enrolled |
| `active_flag` | BOOLEAN | Whether client is currently active |

**Keys**: `client_id` (PK), referenced by `fact_service_visit.client_id`, `fact_claim.client_id`, `fact_funding_allocation.client_id`

### 2. workers.csv

| Field | Type | Description |
|-------|------|-------------|
| `worker_id` | VARCHAR(10) | Unique worker identifier (PK) |
| `worker_name` | VARCHAR(255) | Full name of the worker |
| `worker_type` | VARCHAR(50) | Type of healthcare professional |
| `home_city` | VARCHAR(100) | City where worker is based |
| `weekly_capacity_hours` | DECIMAL(5,1) | Maximum hours per week |
| `hire_date` | DATE | Date of hire |
| `active_flag` | BOOLEAN | Whether worker is currently active |

**Keys**: `worker_id` (PK), referenced by `fact_service_visit.worker_id`

### 3. funders.csv

| Field | Type | Description |
|-------|------|-------------|
| `funder_id` | VARCHAR(10) | Unique funder identifier (PK) |
| `funder_name` | VARCHAR(255) | Name of funding organization |
| `funding_type` | VARCHAR(50) | Type of funding source |
| `claim_limit` | DECIMAL(12,2) | Maximum total claims allowed |
| `documentation_sla_days` | INTEGER | Days allowed for documentation |

**Keys**: `funder_id` (PK), referenced by `fact_claim.funder_id`, `fact_funding_allocation.funder_id`

### 4. funding_allocations.csv

| Field | Type | Description |
|-------|------|-------------|
| `allocation_id` | VARCHAR(12) | Unique allocation identifier (PK) |
| `client_id` | VARCHAR(10) | Client receiving funding (FK) |
| `funder_id` | VARCHAR(10) | Fundder providing funding (FK) |
| `allocation_start_date` | DATE | Start of allocation period |
| `allocation_end_date` | DATE | End of allocation period |
| `allocated_amount` | DECIMAL(12,2) | Total allocated funding |
| `approved_hours` | DECIMAL(10,1) | Approved hours under allocation |

**Keys**: `allocation_id` (PK), composite FK on (`client_id`, `funder_id`)

### 5. service_visits.csv

| Field | Type | Description |
|-------|------|-------------|
| `visit_id` | VARCHAR(12) | Unique visit identifier (PK) |
| `client_id` | VARCHAR(10) | Client receiving service (FK) |
| `worker_id` | VARCHAR(10) | Worker providing service (FK) |
| `service_date` | DATE | Date of the service visit |
| `service_type` | VARCHAR(100) | Type of care service delivered |
| `scheduled_hours` | DECIMAL(5,1) | Scheduled hours for visit |
| `completed_hours` | DECIMAL(5,1) | Actual hours completed |
| `hourly_rate` | DECIMAL(6,2) | Billing rate per hour |
| `visit_status` | VARCHAR(20) | Completed, Cancelled, or Missed |
| `documentation_submitted_date` | DATE | When documentation was submitted |
| `documentation_delay_days` | INTEGER | Days delayed vs SLA |

**Keys**: `visit_id` (PK), FKs to `dim_client`, `dim_worker`, `dim_service`

### 6. claims.csv

| Field | Type | Description |
|-------|------|-------------|
| `claim_id` | VARCHAR(12) | Unique claim identifier (PK) |
| `visit_id` | VARCHAR(12) | Associated service visit (FK) |
| `client_id` | VARCHAR(10) | Client (FK) |
| `funder_id` | VARCHAR(10) | Funding organization (FK) |
| `claim_date` | DATE | Date claim was submitted |
| `claim_amount` | DECIMAL(10,2) | Dollar amount claimed |
| `claim_status` | VARCHAR(20) | Approved, Rejected, or Pending Review |
| `rejection_reason` | VARCHAR(100) | Reason if rejected |
| `submitted_late_flag` | BOOLEAN | Whether submitted beyond SLA |
| `duplicate_candidate_flag` | BOOLEAN | Whether flagged as potential duplicate |

**Keys**: `claim_id` (PK), FKs to `fact_service_visit`, `dim_client`, `dim_funder`

### 7. reconciliation_exceptions.csv

| Field | Type | Description |
|-------|------|-------------|
| `exception_id` | VARCHAR(10) | Unique exception identifier (PK) |
| `claim_id` | VARCHAR(12) | Associated claim (FK) |
| `exception_type` | VARCHAR(50) | Type of reconciliation exception |
| `detected_date` | DATE | When exception was identified |
| `resolved_date` | DATE | When exception was resolved (nullable) |
| `exception_status` | VARCHAR(20) | Open, In Progress, or Resolved |
| `exception_amount` | DECIMAL(10,2) | Financial value of exception |
| `priority` | VARCHAR(10) | High, Medium, or Low |

**Keys**: `exception_id` (PK), FK to `fact_claim`

---

## Star Schema Tables

### Dimension Tables

#### dim_date

| Field | Type | Description |
|-------|------|-------------|
| `date_key` | INTEGER (PK) | Date in YYYYMMDD format |
| `year` | INTEGER | Calendar year |
| `month` | INTEGER | Calendar month |
| `day` | INTEGER | Day of month |
| `day_of_week` | INTEGER | 0=Sunday through 6=Saturday |
| `date_string` | DATE | Actual date value |
| `quarter` | INTEGER | Quarter of year (1-4) |

**Purpose**: Conformed date dimension enabling time-based analysis across all fact tables.

#### dim_client

| Field | Type | Description |
|-------|------|-------------|
| `client_id` | VARCHAR(10) (PK) | Client identifier |
| `client_name` | VARCHAR(255) | Client name |
| `city` | VARCHAR(100) | Client city |
| `service_program` | VARCHAR(100) | Care program type |
| `intake_date` | DATE | Enrollment date |
| `active_flag` | BOOLEAN | Active status |

#### dim_worker

| Field | Type | Description |
|-------|------|-------------|
| `worker_id` | VARCHAR(10) (PK) | Worker identifier |
| `worker_name` | VARCHAR(255) | Worker name |
| `worker_type` | VARCHAR(50) | Healthcare role |
| `home_city` | VARCHAR(100) | Worker's city |
| `weekly_capacity_hours` | DECIMAL(5,1) | Weekly capacity |
| `hire_date` | DATE | Hire date |
| `active_flag` | BOOLEAN | Active status |

#### dim_funder

| Field | Type | Description |
|-------|------|-------------|
| `funder_id` | VARCHAR(10) (PK) | Funder identifier |
| `funder_name` | VARCHAR(255) | Funder organization name |
| `funding_type` | VARCHAR(50) | Funding category |
| `claim_limit` | DECIMAL(12,2) | Maximum claims |
| `documentation_sla_days` | INTEGER | Documentation SLA |

#### dim_service

| Field | Type | Description |
|-------|------|-------------|
| `service_code` | VARCHAR(100) (PK) | Service type code |
| `service_name` | VARCHAR(100) | Service description |

### Fact Tables

#### fact_service_visit

| Field | Type | Description |
|-------|------|-------------|
| `visit_id` | VARCHAR(12) (PK) | Visit identifier |
| `client_id` | VARCHAR(10) (FK) | References dim_client |
| `worker_id` | VARCHAR(10) (FK) | References dim_worker |
| `service_date` | DATE | Date of service |
| `service_type` | VARCHAR(100) (FK) | References dim_service |
| `scheduled_hours` | DECIMAL(5,1) | Scheduled hours |
| `completed_hours` | DECIMAL(5,1) | Actual completed hours |
| `hourly_rate` | DECIMAL(6,2) | Billing rate |
| `visit_status` | VARCHAR(20) | Visit status |
| `documentation_submitted_date` | DATE | Doc submission date |
| `documentation_delay_days` | INTEGER | Days delayed |
| `date_key` | INTEGER (FK) | References dim_date |

#### fact_claim

| Field | Type | Description |
|-------|------|-------------|
| `claim_id` | VARCHAR(12) (PK) | Claim identifier |
| `visit_id` | VARCHAR(12) (FK) | References fact_service_visit |
| `client_id` | VARCHAR(10) (FK) | References dim_client |
| `funder_id` | VARCHAR(10) (FK) | References dim_funder |
| `claim_date` | DATE | Claim submission date |
| `claim_amount` | DECIMAL(10,2) | Claim dollar amount |
| `claim_status` | VARCHAR(20) | Approval status |
| `rejection_reason` | VARCHAR(100) | Rejection reason if applicable |
| `submitted_late_flag` | BOOLEAN | Late submission flag |
| `duplicate_candidate_flag` | BOOLEAN | Duplicate candidate flag |
| `date_key` | INTEGER (FK) | References dim_date |

#### fact_reconciliation_exception

| Field | Type | Description |
|-------|------|-------------|
| `exception_id` | VARCHAR(10) (PK) | Exception identifier |
| `claim_id` | VARCHAR(12) (FK) | References fact_claim |
| `exception_type` | VARCHAR(50) | Exception category |
| `detected_date` | DATE | Detection date |
| `resolved_date` | DATE | Resolution date (nullable) |
| `exception_status` | VARCHAR(20) | Current status |
| `exception_amount` | DECIMAL(10,2) | Financial impact |
| `priority` | VARCHAR(10) | Priority level |
| `date_key` | INTEGER (FK) | References dim_date |

#### fact_funding_allocation

| Field | Type | Description |
|-------|------|-------------|
| `allocation_id` | VARCHAR(12) (PK) | Allocation identifier |
| `client_id` | VARCHAR(10) (FK) | References dim_client |
| `funder_id` | VARCHAR(10) (FK) | References dim_funder |
| `allocation_start_date` | DATE | Period start |
| `allocation_end_date` | DATE | Period end |
| `allocated_amount` | DECIMAL(12,2) | Allocated funding |
| `approved_hours` | DECIMAL(10,1) | Approved hours |
| `date_key` | INTEGER (FK) | References dim_date |

---

## Key Relationships

```
dim_client ←── fact_service_visit → dim_worker
dim_client ←── fact_claim → dim_funder
fact_service_visit → fact_claim
fact_claim → fact_reconciliation_exception
dim_client ←── fact_funding_allocation → dim_funder
dim_date ←── all fact tables
dim_service ←── fact_service_visit
```

All fact tables connect to `dim_date` for time-based analysis. The `dim_service` table serves as a conformed dimension for service types across visit and claim analysis.
