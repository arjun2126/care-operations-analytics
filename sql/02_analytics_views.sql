-- ============================================
-- ANALYTICS VIEWS for Dashboard Consumption
-- ============================================

-- View: Monthly operational summary
CREATE OR REPLACE VIEW vw_monthly_operations AS
SELECT
    d.year,
    d.month,
    COUNT(DISTINCT sv.visit_id) AS total_visits,
    SUM(sv.completed_hours) AS total_completed_hours,
    SUM(sv.completed_hours * sv.hourly_rate) AS total_billed_amount,
    COUNT(DISTINCT c.claim_id) AS total_claims,
    COUNT(DISTINCT CASE WHEN c.claim_status = 'Approved' THEN c.claim_id END) AS approved_claims,
    ROUND(
        COUNT(DISTINCT CASE WHEN c.claim_status = 'Approved' THEN c.claim_id END)::DECIMAL
        / NULLIF(COUNT(DISTINCT c.claim_id), 0) * 100, 1
    ) AS approval_rate_pct,
    COUNT(DISTINCT exc.exception_id) AS exception_count
FROM dim_date d
LEFT JOIN fact_service_visit sv ON d.date_key = sv.date_key AND sv.visit_status = 'Completed'
LEFT JOIN fact_claim c ON d.date_key = c.date_key
LEFT JOIN fact_reconciliation_exception exc ON d.date_key = exc.date_key
WHERE d.year = 2024
GROUP BY d.year, d.month
ORDER BY d.year, d.month;

COMMENT ON VIEW vw_monthly_operations IS 'Monthly rollup of visits, hours, claims, approval rates, and exceptions. Primary dashboard view for monthly trend analysis.';

-- View: Funding utilization by client and funder
CREATE OR REPLACE VIEW vw_funding_utilization AS
SELECT
    fa.client_id,
    fa.funder_id,
    fn.funder_name,
    fn.funding_type,
    fa.allocated_amount,
    COALESCE(SUM(c.claim_amount), 0) AS total_claim_spend,
    ROUND(
        COALESCE(SUM(c.claim_amount), 0) / NULLIF(fa.allocated_amount, 0) * 100, 1
    ) AS utilization_pct,
    fa.allocated_amount - COALESCE(SUM(c.claim_amount), 0) AS remaining_funding,
    fa.approved_hours,
    COALESCE(SUM(sv.completed_hours), 0) AS actual_hours
FROM fact_funding_allocation fa
JOIN dim_funder fn ON fa.funder_id = fn.funder_id
LEFT JOIN fact_claim c ON fa.client_id = c.client_id AND fa.funder_id = c.funder_id AND c.claim_status = 'Approved'
LEFT JOIN fact_service_visit sv ON sv.client_id = fa.client_id AND sv.visit_status = 'Completed'
WHERE fa.allocation_end_date >= CURRENT_DATE
GROUP BY fa.client_id, fa.funder_id, fn.funder_name, fn.funding_type, fa.allocated_amount, fa.approved_hours
ORDER BY utilization_pct DESC;

COMMENT ON VIEW vw_funding_utilization IS 'Shows funding allocation vs approved claim spend per client-funder pair. Key view for identifying over-utilization risk.';

-- View: At-risk clients and funders (approaching 90% utilization)
CREATE OR REPLACE VIEW vw_at_risk_funding AS
SELECT
    fu.client_id,
    fu.funder_id,
    fu.funder_name,
    fu.allocated_amount,
    fu.total_claim_spend,
    fu.utilization_pct,
    fu.remaining_funding
FROM vw_funding_utilization fu
WHERE fu.utilization_pct >= 90
ORDER BY fu.utilization_pct DESC;

COMMENT ON VIEW vw_at_risk_funding IS 'Filters funding_utilization for records at or above 90% utilization. Highlights clients/funders at risk of exceeding allocated funding.';

-- View: Claims rejection analysis by funder
CREATE OR REPLACE VIEW vw_claims_rejection_by_funder AS
SELECT
    c.funder_id,
    fn.funder_name,
    c.claim_status,
    c.rejection_reason,
    COUNT(*) AS claim_count,
    SUM(c.claim_amount) AS total_claim_amount
FROM fact_claim c
JOIN dim_funder fn ON c.funder_id = fn.funder_id
WHERE c.claim_status = 'Rejected' OR c.rejection_reason IS NOT NULL
GROUP BY c.funder_id, fn.funder_name, c.claim_status, c.rejection_reason
ORDER BY c.funder_id, c.claim_status, c.rejection_reason;

COMMENT ON VIEW vw_claims_rejection_by_funder IS 'Breaks down rejected claims by funder and rejection reason. Used to identify systemic rejection patterns.';

-- View: Aging unresolved reconciliation exceptions
CREATE OR REPLACE VIEW vw_aging_exceptions AS
SELECT
    exc.exception_id,
    exc.claim_id,
    exc.exception_type,
    exc.priority,
    exc.exception_amount,
    exc.detected_date,
    exc.resolved_date,
    exc.exception_status,
    CASE
        WHEN exc.resolved_date IS NULL THEN EXTRACT(DAY FROM AGE(CURRENT_DATE, exc.detected_date))
        ELSE EXTRACT(DAY FROM AGE(exc.resolved_date, exc.detected_date))
    END AS days_open,
    CASE
        WHEN exc.resolved_date IS NULL AND EXTRACT(DAY FROM AGE(CURRENT_DATE, exc.detected_date)) > 60 THEN 'Critical'
        WHEN exc.resolved_date IS NULL AND EXTRACT(DAY FROM AGE(CURRENT_DATE, exc.detected_date)) > 30 THEN 'Aging'
        WHEN exc.resolved_date IS NULL THEN 'Recent'
        ELSE 'Resolved'
    END AS aging_category
FROM fact_reconciliation_exception exc
WHERE exc.exception_status != 'Resolved'
ORDER BY exc.priority, days_open DESC;

COMMENT ON VIEW vw_aging_exceptions IS 'Tracks open exceptions with aging categories. Critical = >60 days, Aging = >30 days open. Key for reconciliation risk management.';

-- View: Worker capacity violations
CREATE OR REPLACE VIEW vw_worker_capacity_violations AS
SELECT
    sv.worker_id,
    w.worker_name,
    w.worker_type,
    w.weekly_capacity_hours,
    DATE_TRUNC('week', sv.service_date) AS week_start,
    SUM(sv.completed_hours) AS weekly_completed_hours,
    w.weekly_capacity_hours - SUM(sv.completed_hours) AS hours_remaining,
    CASE
        WHEN SUM(sv.completed_hours) > w.weekly_capacity_hours THEN 'OVER CAPACITY'
        ELSE 'Within Capacity'
    END AS capacity_status
FROM fact_service_visit sv
JOIN dim_worker w ON sv.worker_id = w.worker_id
WHERE sv.visit_status = 'Completed'
GROUP BY sv.worker_id, w.worker_name, w.worker_type, w.weekly_capacity_hours, DATE_TRUNC('week', sv.service_date)
HAVING SUM(sv.completed_hours) > w.weekly_capacity_hours
ORDER BY weekly_completed_hours DESC;

COMMENT ON VIEW vw_worker_capacity_violations IS 'Identifies weeks where a worker completed hours exceed their weekly capacity. Essential for operational capacity planning.';

-- View: Documentation delay trends and rejection correlation
CREATE OR REPLACE VIEW vw_doc_delay_analysis AS
SELECT
    sv.service_date,
    sv.service_type,
    sv.documentation_delay_days,
    COUNT(*) AS visit_count,
    COUNT(DISTINCT c.claim_id) AS claim_count,
    ROUND(
        COUNT(DISTINCT CASE WHEN c.claim_status = 'Rejected' THEN c.claim_id END)::DECIMAL
        / NULLIF(COUNT(DISTINCT c.claim_id), 0) * 100, 1
    ) AS rejection_rate_pct
FROM fact_service_visit sv
LEFT JOIN fact_claim c ON sv.visit_id = c.visit_id
WHERE sv.visit_status = 'Completed' AND sv.documentation_delay_days IS NOT NULL AND sv.documentation_delay_days > 0
GROUP BY sv.service_date, sv.service_type, sv.documentation_delay_days
ORDER BY sv.documentation_delay_days DESC;

COMMENT ON VIEW vw_doc_delay_analysis IS 'Analyzes documentation delay days against rejection rates. Helps quantify the business impact of late documentation.';

-- View: Duplicate claim candidates and financial exposure
CREATE OR REPLACE VIEW vw_duplicate_claim_risk AS
SELECT
    c.claim_id,
    c.visit_id,
    c.client_id,
    c.funder_id,
    c.claim_amount,
    c.claim_status,
    c.submitted_late_flag,
    c.duplicate_candidate_flag,
    c.rejection_reason
FROM fact_claim c
WHERE c.duplicate_candidate_flag = TRUE
ORDER BY c.claim_amount DESC;

COMMENT ON VIEW vw_duplicate_claim_risk IS 'Lists all duplicate candidate claims and their financial exposure. Used to quantify revenue leakage risk from potential duplicates.';

-- View: Client-level service summary
CREATE OR REPLACE VIEW vw_client_service_summary AS
SELECT
    c.client_id,
    c.client_name,
    c.city,
    c.service_program,
    COUNT(sv.visit_id) AS total_visits,
    SUM(sv.completed_hours) AS total_hours,
    SUM(sv.completed_hours * sv.hourly_rate) AS total_billed,
    COUNT(DISTINCT c2.claim_id) AS total_claims,
    ROUND(AVG(sv.documentation_delay_days), 1) AS avg_doc_delay_days
FROM dim_client c
LEFT JOIN fact_service_visit sv ON c.client_id = sv.client_id
LEFT JOIN fact_claim c2 ON c.client_id = c2.client_id
WHERE c.active_flag = TRUE
GROUP BY c.client_id, c.client_name, c.city, c.service_program
ORDER BY total_billed DESC;

COMMENT ON VIEW vw_client_service_summary IS 'Client-level rollup of visits, hours, billing, and documentation delays. Useful for account management and client-specific reporting.';
