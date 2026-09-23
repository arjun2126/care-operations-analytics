-- ============================================
-- PRODUCTION-STYLE ANALYSIS QUERIES
-- ============================================

-- Query 1: Monthly visits, completed hours, claim dollars, approval rate, exception count
-- Purpose: Executive dashboard - track monthly operational performance
SELECT
    d.year,
    d.month,
    d.month || '/' || d.year AS month_label,
    COUNT(DISTINCT sv.visit_id) AS total_visits,
    SUM(sv.completed_hours) AS completed_hours,
    COALESCE(SUM(sv.completed_hours * sv.hourly_rate), 0) AS billed_amount,
    COUNT(DISTINCT c.claim_id) AS total_claims,
    COALESCE(SUM(c.claim_amount), 0) AS total_claim_dollars,
    ROUND(
        COUNT(DISTINCT CASE WHEN c.claim_status = 'Approved' THEN c.claim_id END)::DECIMAL
        / NULLIF(COUNT(DISTINCT c.claim_id), 0) * 100, 1
    ) AS approval_rate_pct,
    COUNT(DISTINCT exc.exception_id) AS exception_count
FROM dim_date d
LEFT JOIN fact_service_visit sv ON d.date_key = sv.date_key
LEFT JOIN fact_claim c ON d.date_key = c.date_key
LEFT JOIN fact_reconciliation_exception exc ON d.date_key = exc.date_key
WHERE d.year = 2024 AND sv.visit_status = 'Completed'
GROUP BY d.year, d.month
ORDER BY d.year, d.month;

-- Query 2: Funding allocation vs approved claim spend, utilization %, remaining by client and funder
-- Purpose: Identify funders and clients approaching funding limits
SELECT
    fa.client_id,
    fa.funder_id,
    fa.allocated_amount,
    COALESCE(SUM(c.claim_amount), 0) AS approved_spend,
    ROUND(
        COALESCE(SUM(c.claim_amount), 0) / NULLIF(fa.allocated_amount, 0) * 100, 1
    ) AS utilization_pct,
    fa.allocated_amount - COALESCE(SUM(c.claim_amount), 0) AS remaining_funding,
    fa.approved_hours,
    COALESCE(SUM(sv.completed_hours), 0) AS actual_hours_billed
FROM fact_funding_allocation fa
LEFT JOIN fact_claim c ON fa.client_id = c.client_id
    AND fa.funder_id = c.funder_id AND c.claim_status = 'Approved'
LEFT JOIN fact_service_visit sv ON fa.client_id = sv.client_id AND sv.visit_status = 'Completed'
GROUP BY fa.client_id, fa.funder_id, fa.allocated_amount, fa.approved_hours
ORDER BY utilization_pct DESC;

-- Query 3: Top clients/funders at risk of exceeding 90% allocated funding
-- Purpose: Proactive alert for potential budget overruns
SELECT
    fa.client_id,
    fa.funder_id,
    fn.funder_name,
    fa.allocated_amount,
    COALESCE(SUM(c.claim_amount), 0) AS total_claim_spend,
    ROUND(
        COALESCE(SUM(c.claim_amount), 0) / NULLIF(fa.allocated_amount, 0) * 100, 1
    ) AS utilization_pct,
    fa.allocated_amount - COALESCE(SUM(c.claim_amount), 0) AS remaining_funding
FROM fact_funding_allocation fa
JOIN dim_funder fn ON fa.funder_id = fn.funder_id
LEFT JOIN fact_claim c ON fa.client_id = c.client_id AND fa.funder_id = c.funder_id AND c.claim_status = 'Approved'
GROUP BY fa.client_id, fa.funder_id, fn.funder_name, fa.allocated_amount
HAVING COALESCE(SUM(c.claim_amount), 0) / NULLIF(fa.allocated_amount, 0) >= 0.90
ORDER BY utilization_pct DESC
LIMIT 20;

-- Query 4: Claims rejection rate by funder and rejection reason
-- Purpose: Identify systemic issues with specific funders or documentation
SELECT
    c.funder_id,
    fn.funder_name,
    c.rejection_reason,
    COUNT(*) AS rejected_claims,
    SUM(c.claim_amount) AS rejected_amount,
    ROUND(
        COUNT(*)::DECIMAL / NULLIF(COUNT(DISTINCT CASE WHEN c.funder_id = c.funder_id THEN c.claim_id END), 0) * 100, 1
    ) AS rejection_rate_pct
FROM fact_claim c
JOIN dim_funder fn ON c.funder_id = fn.funder_id
WHERE c.claim_status = 'Rejected'
GROUP BY c.funder_id, fn.funder_name, c.rejection_reason
ORDER BY rejected_claims DESC;

-- Query 5: Aging unresolved reconciliation exceptions by priority
-- Purpose: Prioritize reconciliation team effort and financial exposure
SELECT
    priority,
    COUNT(*) AS open_exceptions,
    SUM(exception_amount) AS total_exposure,
    ROUND(AVG(EXTRACT(DAY FROM AGE(CURRENT_DATE, detected_date))), 1) AS avg_days_open,
    MAX(EXTRACT(DAY FROM AGE(CURRENT_DATE, detected_date))) AS max_days_open
FROM fact_reconciliation_exception
WHERE exception_status != 'Resolved'
GROUP BY priority
ORDER BY CASE priority WHEN 'High' THEN 1 WHEN 'Medium' THEN 2 ELSE 3 END;

-- Query 6: Workers with weekly completed hours above their capacity
-- Purpose: Operational capacity constraint alert
SELECT
    sv.worker_id,
    w.worker_name,
    w.worker_type,
    w.weekly_capacity_hours,
    DATE_TRUNC('week', sv.service_date) AS week_start,
    SUM(sv.completed_hours) AS weekly_completed_hours,
    ROUND(SUM(sv.completed_hours) - w.weekly_capacity_hours, 1) AS overtime_hours
FROM fact_service_visit sv
JOIN dim_worker w ON sv.worker_id = w.worker_id
WHERE sv.visit_status = 'Completed'
GROUP BY sv.worker_id, w.worker_name, w.worker_type, w.weekly_capacity_hours, DATE_TRUNC('week', sv.service_date)
HAVING SUM(sv.completed_hours) > w.weekly_capacity_hours
ORDER BY overtime_hours DESC;

-- Query 7: Documentation delay trends and relationship with rejected claims
-- Purpose: Quantify business impact of late documentation on claim outcomes
SELECT
    sv.documentation_delay_days,
    COUNT(*) AS total_visits,
    COUNT(DISTINCT c.claim_id) AS total_claims,
    COUNT(DISTINCT CASE WHEN c.claim_status = 'Rejected' THEN c.claim_id END) AS rejected_claims,
    ROUND(
        COUNT(DISTINCT CASE WHEN c.claim_status = 'Rejected' THEN c.claim_id END)::DECIMAL
        / NULLIF(COUNT(DISTINCT c.claim_id), 0) * 100, 1
    ) AS rejection_rate_pct
FROM fact_service_visit sv
LEFT JOIN fact_claim c ON sv.visit_id = c.visit_id
WHERE sv.visit_status = 'Completed' AND sv.documentation_delay_days IS NOT NULL AND sv.documentation_delay_days > 0
GROUP BY sv.documentation_delay_days
ORDER BY sv.documentation_delay_days;

-- Query 8: Duplicate-claim candidates and their financial exposure
-- Purpose: Quantify revenue leakage risk from potential duplicate claims
SELECT
    c.claim_id,
    c.visit_id,
    c.client_id,
    c.funder_id,
    c.claim_amount,
    c.claim_status,
    c.submitted_late_flag,
    c.duplicate_candidate_flag,
    c.rejection_reason,
    c.claim_date
FROM fact_claim c
WHERE c.duplicate_candidate_flag = TRUE
ORDER BY c.claim_amount DESC;

-- Bonus Query: Overall business KPIs
SELECT
    COUNT(DISTINCT sv.visit_id) AS total_visits,
    COUNT(DISTINCT CASE WHEN sv.visit_status = 'Completed' THEN sv.visit_id END) AS completed_visits,
    ROUND(
        COUNT(DISTINCT CASE WHEN sv.visit_status = 'Completed' THEN sv.visit_id END)::DECIMAL
        / NULLIF(COUNT(DISTINCT sv.visit_id), 0) * 100, 1
    ) AS completion_rate_pct,
    SUM(sv.completed_hours) AS total_hours,
    SUM(sv.completed_hours * sv.hourly_rate) AS total_billed,
    COUNT(DISTINCT c.claim_id) AS total_claims,
    ROUND(
        COUNT(DISTINCT CASE WHEN c.claim_status = 'Approved' THEN c.claim_id END)::DECIMAL
        / NULLIF(COUNT(DISTINCT c.claim_id), 0) * 100, 1
    ) AS overall_approval_rate_pct,
    COUNT(DISTINCT exc.exception_id) AS total_exceptions,
    SUM(exc.exception_amount) AS total_exception_value
FROM fact_service_visit sv
LEFT JOIN fact_claim c ON sv.visit_id = c.visit_id
LEFT JOIN fact_reconciliation_exception exc ON c.claim_id = exc.claim_id;
