-- ============================================
-- STAR SCHEMA: Dimension Tables
-- ============================================

-- Date dimension for all dates in 2024
CREATE TABLE IF NOT EXISTS dim_date (
    date_key INTEGER PRIMARY KEY,
    year INTEGER NOT NULL,
    month INTEGER NOT NULL,
    day INTEGER NOT NULL,
    day_of_week INTEGER NOT NULL CHECK (day_of_week BETWEEN 0 AND 6),
    date_string DATE NOT NULL UNIQUE,
    quarter INTEGER NOT NULL CHECK (quarter BETWEEN 1 AND 4)
);

COMMENT ON TABLE dim_date IS 'Date dimension covering all service dates in 2024. Used for date-based filtering and aggregation across all fact tables.';

-- Client dimension
CREATE TABLE IF NOT EXISTS dim_client (
    client_id VARCHAR(10) PRIMARY KEY,
    client_name VARCHAR(255) NOT NULL,
    city VARCHAR(100),
    service_program VARCHAR(100),
    intake_date DATE,
    active_flag BOOLEAN NOT NULL DEFAULT TRUE
);

COMMENT ON TABLE dim_client IS 'Master client dimension. Tracks client demographics and program enrollment. Serves as FK in fact_service_visit and fact_claim.';

-- Worker dimension
CREATE TABLE IF NOT EXISTS dim_worker (
    worker_id VARCHAR(10) PRIMARY KEY,
    worker_name VARCHAR(255) NOT NULL,
    worker_type VARCHAR(50) NOT NULL,
    home_city VARCHAR(100),
    weekly_capacity_hours DECIMAL(5,1) NOT NULL,
    hire_date DATE,
    active_flag BOOLEAN NOT NULL DEFAULT TRUE
);

COMMENT ON TABLE dim_worker IS 'Master worker dimension. Contains worker type and weekly capacity. Used to identify capacity constraint violations in fact_service_visit.';

-- Funder dimension
CREATE TABLE IF NOT EXISTS dim_funder (
    funder_id VARCHAR(10) PRIMARY KEY,
    funder_name VARCHAR(255) NOT NULL,
    funding_type VARCHAR(50) NOT NULL,
    claim_limit DECIMAL(12,2) NOT NULL,
    documentation_sla_days INTEGER NOT NULL
);

COMMENT ON TABLE dim_funder IS 'Master funder dimension. Contains funding limits and documentation SLA. Used to track funding utilization and SLA compliance.';

-- Service dimension (conformed dimension for service types)
CREATE TABLE IF NOT EXISTS dim_service (
    service_code VARCHAR(100) PRIMARY KEY,
    service_name VARCHAR(100) NOT NULL
);

COMMENT ON TABLE dim_service IS 'Conformed dimension for service types. Enables cross-fact analysis of service type performance.';

-- ============================================
-- STAR SCHEMA: Fact Tables
-- ============================================

-- Fact: Service Visits
CREATE TABLE IF NOT EXISTS fact_service_visit (
    visit_id VARCHAR(12) PRIMARY KEY,
    client_id VARCHAR(10) NOT NULL REFERENCES dim_client(client_id),
    worker_id VARCHAR(10) NOT NULL REFERENCES dim_worker(worker_id),
    service_date DATE NOT NULL,
    service_type VARCHAR(100) NOT NULL REFERENCES dim_service(service_code),
    scheduled_hours DECIMAL(5,1) NOT NULL CHECK (scheduled_hours >= 0),
    completed_hours DECIMAL(5,1) NOT NULL CHECK (completed_hours >= 0),
    hourly_rate DECIMAL(6,2) NOT NULL CHECK (hourly_rate >= 0),
    visit_status VARCHAR(20) NOT NULL CHECK (visit_status IN ('Completed', 'Cancelled', 'Missed')),
    documentation_submitted_date DATE,
    documentation_delay_days INTEGER,
    date_key INTEGER REFERENCES dim_date(date_key)
);

CREATE INDEX idx_fact_sv_client ON fact_service_visit(client_id);
CREATE INDEX idx_fact_sv_worker ON fact_service_visit(worker_id);
CREATE INDEX idx_fact_sv_date ON fact_service_visit(date_key);
CREATE INDEX idx_fact_sv_status ON fact_service_visit(visit_status);
CREATE INDEX idx_fact_sv_servicetype ON fact_service_visit(service_type);

COMMENT ON TABLE fact_service_visit IS 'Primary fact table for in-home service visits. Links to dim_client, dim_worker, dim_service, and dim_date. Contains hours, rates, and documentation metadata.';

-- Fact: Claims
CREATE TABLE IF NOT EXISTS fact_claim (
    claim_id VARCHAR(12) PRIMARY KEY,
    visit_id VARCHAR(12) NOT NULL REFERENCES fact_service_visit(visit_id),
    client_id VARCHAR(10) NOT NULL REFERENCES dim_client(client_id),
    funder_id VARCHAR(10) NOT NULL REFERENCES dim_funder(funder_id),
    claim_date DATE NOT NULL,
    claim_amount DECIMAL(10,2) NOT NULL CHECK (claim_amount >= 0),
    claim_status VARCHAR(20) NOT NULL CHECK (claim_status IN ('Approved', 'Rejected', 'Pending Review')),
    rejection_reason VARCHAR(100),
    submitted_late_flag BOOLEAN NOT NULL DEFAULT FALSE,
    duplicate_candidate_flag BOOLEAN NOT NULL DEFAULT FALSE,
    date_key INTEGER REFERENCES dim_date(date_key)
);

CREATE INDEX idx_fact_claim_visit ON fact_claim(visit_id);
CREATE INDEX idx_fact_claim_client ON fact_claim(client_id);
CREATE INDEX idx_fact_claim_funder ON fact_claim(funder_id);
CREATE INDEX idx_fact_claim_status ON fact_claim(claim_status);
CREATE INDEX idx_fact_claim_date ON fact_claim(date_key);
CREATE INDEX idx_fact_claim_dup ON fact_claim(duplicate_candidate_flag) WHERE duplicate_candidate_flag = TRUE;

COMMENT ON TABLE fact_claim IS 'Claim fact table linking visits to funders. Tracks approval/rejection status, late submission flags, and duplicate candidates for revenue cycle analysis.';

-- Fact: Reconciliation Exceptions
CREATE TABLE IF NOT EXISTS fact_reconciliation_exception (
    exception_id VARCHAR(10) PRIMARY KEY,
    claim_id VARCHAR(12) NOT NULL REFERENCES fact_claim(claim_id),
    exception_type VARCHAR(50) NOT NULL,
    detected_date DATE NOT NULL,
    resolved_date DATE,
    exception_status VARCHAR(20) NOT NULL CHECK (exception_status IN ('Open', 'In Progress', 'Resolved')),
    exception_amount DECIMAL(10,2) NOT NULL CHECK (exception_amount >= 0),
    priority VARCHAR(10) NOT NULL CHECK (priority IN ('High', 'Medium', 'Low')),
    date_key INTEGER REFERENCES dim_date(date_key)
);

CREATE INDEX idx_fact_exc_claim ON fact_reconciliation_exception(claim_id);
CREATE INDEX idx_fact_exc_status ON fact_reconciliation_exception(exception_status);
CREATE INDEX idx_fact_exc_priority ON fact_reconciliation_exception(priority);
CREATE INDEX idx_fact_exc_detected ON fact_reconciliation_exception(detected_date);
CREATE INDEX idx_fact_exc_unresolved ON fact_reconciliation_exception(exception_status) WHERE exception_status != 'Resolved';

COMMENT ON TABLE fact_reconciliation_exception IS 'Aging and resolution tracking for reconciliation exceptions. Used to monitor open exceptions and financial exposure by priority.';

-- Fact: Funding Allocations
CREATE TABLE IF NOT EXISTS fact_funding_allocation (
    allocation_id VARCHAR(12) PRIMARY KEY,
    client_id VARCHAR(10) NOT NULL REFERENCES dim_client(client_id),
    funder_id VARCHAR(10) NOT NULL REFERENCES dim_funder(funder_id),
    allocation_start_date DATE NOT NULL,
    allocation_end_date DATE NOT NULL,
    allocated_amount DECIMAL(12,2) NOT NULL CHECK (allocated_amount >= 0),
    approved_hours DECIMAL(10,1) NOT NULL CHECK (approved_hours >= 0),
    date_key INTEGER REFERENCES dim_date(date_key)
);

CREATE INDEX idx_fact_fa_client ON fact_funding_allocation(client_id);
CREATE INDEX idx_fact_fa_funder ON fact_funding_allocation(funder_id);
CREATE INDEX idx_fact_fa_date ON fact_funding_allocation(date_key);

COMMENT ON TABLE fact_funding_allocation IS 'Funding allocation fact. Tracks how much funding each client receives from each funder. Basis for utilization and remaining funding analysis.';
