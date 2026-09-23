import logging
from typing import Dict

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

from src.config import config
from src.transform import save_processed_data, apply_all_cleaning

logger = logging.getLogger(__name__)


def get_engine() -> create_engine:
    return create_engine(config.database_url, echo=False)


def load_dimensions(engine, cleaned: Dict[str, pd.DataFrame]) -> None:
    with engine.connect() as conn:
        conn.execute(text("BEGIN"))
        try:
            _load_dim_client(conn, cleaned["clients"])
            _load_dim_worker(conn, cleaned["workers"])
            _load_dim_funder(conn, cleaned["funders"])
            _load_dim_service(conn, cleaned["service_visits"])
            _load_dim_date(conn)
            conn.execute(text("COMMIT"))
        except Exception:
            conn.execute(text("ROLLBACK"))
            raise


def _load_dim_client(conn, df: pd.DataFrame) -> None:
    if df.empty:
        return
    records = df.to_dict("records")
    values = []
    for r in records:
        values.append((
            r["client_id"], r["client_name"], r["city"], r["service_program"],
            str(r["intake_date"]) if pd.notna(r["intake_date"]) else None,
            bool(r["active_flag"]),
        ))
    conn.execute(text("""
        INSERT INTO dim_client (client_id, client_name, city, service_program, intake_date, active_flag)
        VALUES (:v1, :v2, :v3, :v4, :v5, :v6)
        ON CONFLICT (client_id) DO UPDATE SET
            client_name = EXCLUDED.client_name, city = EXCLUDED.city,
            service_program = EXCLUDED.service_program, intake_date = EXCLUDED.intake_date,
            active_flag = EXCLUDED.active_flag
    """), values)
    logger.info(f"Loaded {len(values)} dim_client rows")


def _load_dim_worker(conn, df: pd.DataFrame) -> None:
    if df.empty:
        return
    records = df.to_dict("records")
    values = []
    for r in records:
        values.append((
            r["worker_id"], r["worker_name"], r["worker_type"], r["home_city"],
            float(r["weekly_capacity_hours"]), str(r["hire_date"]) if pd.notna(r["hire_date"]) else None,
            bool(r["active_flag"]),
        ))
    conn.execute(text("""
        INSERT INTO dim_worker (worker_id, worker_name, worker_type, home_city, weekly_capacity_hours, hire_date, active_flag)
        VALUES (:v1, :v2, :v3, :v4, :v5, :v6, :v7)
        ON CONFLICT (worker_id) DO UPDATE SET
            worker_name = EXCLUDED.worker_name, worker_type = EXCLUDED.worker_type,
            home_city = EXCLUDED.home_city, weekly_capacity_hours = EXCLUDED.weekly_capacity_hours,
            hire_date = EXCLUDED.hire_date, active_flag = EXCLUDED.active_flag
    """), values)
    logger.info(f"Loaded {len(values)} dim_worker rows")


def _load_dim_funder(conn, df: pd.DataFrame) -> None:
    if df.empty:
        return
    records = df.to_dict("records")
    values = []
    for r in records:
        values.append((
            r["funder_id"], r["funder_name"], r["funding_type"],
            float(r["claim_limit"]), int(r["documentation_sla_days"]),
        ))
    conn.execute(text("""
        INSERT INTO dim_funder (funder_id, funder_name, funding_type, claim_limit, documentation_sla_days)
        VALUES (:v1, :v2, :v3, :v4, :v5)
        ON CONFLICT (funder_id) DO UPDATE SET
            funder_name = EXCLUDED.funder_name, funding_type = EXCLUDED.funding_type,
            claim_limit = EXCLUDED.claim_limit, documentation_sla_days = EXCLUDED.documentation_sla_days
    """), values)
    logger.info(f"Loaded {len(values)} dim_funder rows")


def _load_dim_service(conn, df: pd.DataFrame) -> None:
    if df.empty:
        return
    service_types = df["service_type"].dropna().unique()
    values = []
    for st in service_types:
        values.append((st, st))
    conn.execute(text("""
        INSERT INTO dim_service (service_code, service_name)
        VALUES (:v1, :v2)
        ON CONFLICT (service_code) DO NOTHING
    """), values)
    logger.info(f"Loaded {len(values)} dim_service rows")


def _load_dim_date(conn) -> None:
    from datetime import date, timedelta
    start = date(2024, 1, 1)
    end = date(2024, 12, 31)
    values = []
    d = start
    while d <= end:
        values.append((
            int(d.strftime("%Y%m%d")), d.year, d.month, d.day, d.weekday(),
            d.strftime("%Y-%m-%d"), d.strftime("%Q").replace("%Q", ""),  # quarter placeholder
        ))
        d += timedelta(days=1)
    conn.execute(text("""
        INSERT INTO dim_date (date_key, year, month, day, day_of_week, date_string, quarter)
        VALUES (:v1, :v2, :v3, :v4, :v5, :v6, :v7)
        ON CONFLICT (date_key) DO NOTHING
    """), values)
    logger.info(f"Loaded {len(values)} dim_date rows")


def load_facts(engine, cleaned: Dict[str, pd.DataFrame]) -> None:
    with engine.connect() as conn:
        conn.execute(text("BEGIN"))
        try:
            _load_fact_service_visit(conn, cleaned["service_visits"])
            _load_fact_claim(conn, cleaned["claims"])
            _load_fact_reconciliation_exception(conn, cleaned["reconciliation_exceptions"])
            _load_fact_funding_allocation(conn, cleaned["funding_allocations"])
            conn.execute(text("COMMIT"))
        except Exception:
            conn.execute(text("ROLLBACK"))
            raise


def _load_fact_service_visit(conn, df: pd.DataFrame) -> None:
    if df.empty:
        return
    records = df.to_dict("records")
    values = []
    for r in records:
        doc_sub = str(r["documentation_submitted_date"]) if pd.notna(r.get("documentation_submitted_date")) else None
        doc_delay = int(r["documentation_delay_days"]) if pd.notna(r.get("documentation_delay_days")) else None
        values.append((
            r["visit_id"], r["client_id"], r["worker_id"],
            str(r["service_date"]), r["service_type"],
            float(r["scheduled_hours"]), float(r["completed_hours"]),
            float(r["hourly_rate"]), r["visit_status"],
            doc_sub, doc_delay,
            int(str(r["service_date"]).replace("-", "")) if pd.notna(r.get("service_date")) else None,
        ))
    conn.execute(text("""
        INSERT INTO fact_service_visit (visit_id, client_id, worker_id, service_date, service_type,
            scheduled_hours, completed_hours, hourly_rate, visit_status,
            documentation_submitted_date, documentation_delay_days, date_key)
        VALUES (:v1, :v2, :v3, :v4, :v5, :v6, :v7, :v8, :v9, :v10, :v11, :v12)
        ON CONFLICT (visit_id) DO UPDATE SET
            client_id = EXCLUDED.client_id, worker_id = EXCLUDED.worker_id,
            service_type = EXCLUDED.service_type, scheduled_hours = EXCLUDED.scheduled_hours,
            completed_hours = EXCLUDED.completed_hours, hourly_rate = EXCLUDED.hourly_rate,
            visit_status = EXCLUDED.visit_status, documentation_submitted_date = EXCLUDED.documentation_submitted_date,
            documentation_delay_days = EXCLUDED.documentation_delay_days, date_key = EXCLUDED.date_key
    """), values)
    logger.info(f"Loaded {len(values)} fact_service_visit rows")


def _load_fact_claim(conn, df: pd.DataFrame) -> None:
    if df.empty:
        return
    records = df.to_dict("records")
    values = []
    for r in records:
        values.append((
            r["claim_id"], r["visit_id"], r["client_id"], r["funder_id"],
            str(r["claim_date"]), float(r["claim_amount"]), r["claim_status"],
            r.get("rejection_reason"), bool(r.get("submitted_late_flag", False)),
            bool(r.get("duplicate_candidate_flag", False)),
            int(str(r["claim_date"]).replace("-", "")) if pd.notna(r.get("claim_date")) else None,
        ))
    conn.execute(text("""
        INSERT INTO fact_claim (claim_id, visit_id, client_id, funder_id, claim_date, claim_amount,
            claim_status, rejection_reason, submitted_late_flag, duplicate_candidate_flag, date_key)
        VALUES (:v1, :v2, :v3, :v4, :v5, :v6, :v7, :v8, :v9, :v10, :v11)
        ON CONFLICT (claim_id) DO UPDATE SET
            visit_id = EXCLUDED.visit_id, client_id = EXCLUDED.client_id, funder_id = EXCLUDED.funder_id,
            claim_amount = EXCLUDED.claim_amount, claim_status = EXCLUDED.claim_status,
            rejection_reason = EXCLUDED.rejection_reason, submitted_late_flag = EXCLUDED.submitted_late_flag,
            duplicate_candidate_flag = EXCLUDED.duplicate_candidate_flag, date_key = EXCLUDED.date_key
    """), values)
    logger.info(f"Loaded {len(values)} fact_claim rows")


def _load_fact_reconciliation_exception(conn, df: pd.DataFrame) -> None:
    if df.empty:
        return
    records = df.to_dict("records")
    values = []
    for r in records:
        resolved = str(r["resolved_date"]) if pd.notna(r.get("resolved_date")) else None
        values.append((
            r["exception_id"], r["claim_id"], r["exception_type"],
            str(r["detected_date"]), resolved, r["exception_status"],
            float(r["exception_amount"]), r["priority"],
            int(str(r["detected_date"]).replace("-", "")) if pd.notna(r.get("detected_date")) else None,
        ))
    conn.execute(text("""
        INSERT INTO fact_reconciliation_exception (exception_id, claim_id, exception_type,
            detected_date, resolved_date, exception_status, exception_amount, priority, date_key)
        VALUES (:v1, :v2, :v3, :v4, :v5, :v6, :v7, :v8, :v9)
        ON CONFLICT (exception_id) DO UPDATE SET
            claim_id = EXCLUDED.claim_id, exception_type = EXCLUDED.exception_type,
            resolved_date = EXCLUDED.resolved_date, exception_status = EXCLUDED.exception_status,
            exception_amount = EXCLUDED.exception_amount, priority = EXCLUDED.priority, date_key = EXCLUDED.date_key
    """), values)
    logger.info(f"Loaded {len(values)} fact_reconciliation_exception rows")


def _load_fact_funding_allocation(conn, df: pd.DataFrame) -> None:
    if df.empty:
        return
    records = df.to_dict("records")
    values = []
    for r in records:
        start = str(r["allocation_start_date"]) if pd.notna(r.get("allocation_start_date")) else None
        end = str(r["allocation_end_date"]) if pd.notna(r.get("allocation_end_date")) else None
        values.append((
            r["allocation_id"], r["client_id"], r["funder_id"],
            start, end, float(r["allocated_amount"]), float(r["approved_hours"]),
            int(str(r["allocation_start_date"]).replace("-", "")) if pd.notna(r.get("allocation_start_date")) else None,
        ))
    conn.execute(text("""
        INSERT INTO fact_funding_allocation (allocation_id, client_id, funder_id, allocation_start_date,
            allocation_end_date, allocated_amount, approved_hours, date_key)
        VALUES (:v1, :v2, :v3, :v4, :v5, :v6, :v7, :v8)
        ON CONFLICT (allocation_id) DO UPDATE SET
            client_id = EXCLUDED.client_id, funder_id = EXCLUDED.funder_id,
            allocation_start_date = EXCLUDED.allocation_start_date, allocation_end_date = EXCLUDED.allocation_end_date,
            allocated_amount = EXCLUDED.allocated_amount, approved_hours = EXCLUDED.approved_hours, date_key = EXCLUDED.date_key
    """), values)
    logger.info(f"Loaded {len(values)} fact_funding_allocation rows")


def run_pipeline():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    from src.generate_data import generate_all_data, save_raw_data
    from src.quality_checks import run_all_checks

    logger.info("Starting pipeline...")
    data = generate_all_data()
    save_raw_data(data)
    logger.info("Running data quality checks...")
    run_all_checks(data)
    logger.info("Applying cleaning rules...")
    cleaned, rejected = apply_all_cleaning(data)
    save_processed_data(cleaned, rejected)

    try:
        engine = get_engine()
        logger.info("Loading dimensions...")
        load_dimensions(engine, cleaned)
        logger.info("Loading facts...")
        load_facts(engine, cleaned)
        logger.info("Pipeline completed successfully")
    except Exception as e:
        logger.error(f"Database loading failed: {e}. Ensure PostgreSQL is running via Docker Compose.")
        logger.info("Data files have been generated and cleaned successfully.")
