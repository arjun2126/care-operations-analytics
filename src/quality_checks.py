import logging
import os
from typing import Dict, List, Tuple

import pandas as pd

from src.config import config

logger = logging.getLogger(__name__)

REQUIRED_COLUMNS = {
    "clients": ["client_id", "client_name", "city", "service_program", "intake_date", "active_flag"],
    "workers": ["worker_id", "worker_name", "worker_type", "home_city", "weekly_capacity_hours", "hire_date", "active_flag"],
    "funders": ["funder_id", "funder_name", "funding_type", "claim_limit", "documentation_sla_days"],
    "funding_allocations": ["allocation_id", "client_id", "funder_id", "allocation_start_date", "allocation_end_date", "allocated_amount", "approved_hours"],
    "service_visits": ["visit_id", "client_id", "worker_id", "service_date", "service_type", "scheduled_hours", "completed_hours", "hourly_rate", "visit_status"],
    "claims": ["claim_id", "visit_id", "client_id", "funder_id", "claim_date", "claim_amount", "claim_status"],
    "reconciliation_exceptions": ["exception_id", "claim_id", "exception_type", "detected_date", "exception_status", "exception_amount", "priority"],
}


def check_required_columns(df: pd.DataFrame, table_name: str) -> List[dict]:
    issues = []
    required = REQUIRED_COLUMNS.get(table_name, [])
    missing = [col for col in required if col not in df.columns]
    if missing:
        issues.append({
            "check": "required_columns",
            "table": table_name,
            "status": "FAIL",
            "detail": f"Missing columns: {missing}",
        })
    else:
        issues.append({
            "check": "required_columns",
            "table": table_name,
            "status": "PASS",
            "detail": f"All required columns present for {table_name}",
        })
    return issues


def check_nulls_in_required(df: pd.DataFrame, table_name: str, required_fields: List[str] = None) -> List[dict]:
    issues = []
    fields = required_fields or REQUIRED_COLUMNS.get(table_name, [])
    null_counts = df[fields].isnull().sum()
    for field, count in null_counts.items():
        if count > 0:
            issues.append({
                "check": "null_check",
                "table": table_name,
                "status": "WARN",
                "detail": f"Field '{field}' has {count} null values",
            })
    if not any(i["status"] == "WARN" for i in issues):
        issues.append({
            "check": "null_check",
            "table": table_name,
            "status": "PASS",
            "detail": f"No nulls in required fields for {table_name}",
        })
    return issues


def check_unique_ids(df: pd.DataFrame, id_column: str, table_name: str) -> List[dict]:
    issues = []
    if id_column in df.columns:
        dup_count = df[id_column].duplicated().sum()
        if dup_count > 0:
            issues.append({
                "check": "unique_id",
                "table": table_name,
                "status": "FAIL",
                "detail": f"{dup_count} duplicate values in {id_column}",
            })
        else:
            issues.append({
                "check": "unique_id",
                "table": table_name,
                "status": "PASS",
                "detail": f"All {id_column} values are unique",
            })
    return issues


def check_date_parsable(df: pd.DataFrame, date_columns: List[str], table_name: str) -> List[dict]:
    issues = []
    for col in date_columns:
        if col in df.columns:
            try:
                pd.to_datetime(df[col], errors="raise")
                issues.append({
                    "check": "date_parsable",
                    "table": table_name,
                    "status": "PASS",
                    "detail": f"Column '{col}' dates are parseable",
                })
            except (ValueError, TypeError):
                issues.append({
                    "check": "date_parsable",
                    "table": table_name,
                    "status": "WARN",
                    "detail": f"Column '{col}' contains unparseable dates",
                })
    return issues


def check_non_negative(df: pd.DataFrame, columns: List[str], table_name: str) -> List[dict]:
    issues = []
    for col in columns:
        if col in df.columns:
            negative = (pd.to_numeric(df[col], errors="coerce") < 0).sum()
            if negative > 0:
                issues.append({
                    "check": "non_negative",
                    "table": table_name,
                    "status": "WARN",
                    "detail": f"Column '{col}' has {negative} negative values",
                })
    if not any(i["status"] == "WARN" for i in issues):
        issues.append({
            "check": "non_negative",
            "table": table_name,
            "status": "PASS",
            "detail": f"All monetary/hours values are non-negative for {table_name}",
        })
    return issues


def check_completed_hours_tolerance(df: pd.DataFrame, table_name: str = "service_visits") -> List[dict]:
    issues = []
    if "completed_hours" not in df.columns or "scheduled_hours" not in df.columns:
        return issues
    tolerance = 0.2
    over_tolerance = df[
        (df["completed_hours"] > df["scheduled_hours"] * (1 + tolerance)) &
        (df["visit_status"] == "Completed")
    ]
    if len(over_tolerance) > 0:
        issues.append({
            "check": "completed_hours_tolerance",
            "table": table_name,
            "status": "WARN",
            "detail": f"{len(over_tolerance)} visits exceed {tolerance*100:.0f}% tolerance above scheduled hours",
        })
    else:
        issues.append({
            "check": "completed_hours_tolerance",
            "table": table_name,
            "status": "PASS",
            "detail": "No completed hours exceed tolerance",
        })
    return issues


def check_foreign_keys(
    df: pd.DataFrame, fk_column: str, ref_df: pd.DataFrame, ref_column: str, table_name: str
) -> List[dict]:
    issues = []
    if fk_column not in df.columns or ref_column not in ref_df.columns:
        return issues
    valid_ids = set(ref_df[ref_column].dropna().unique())
    invalid_ids = set(df[fk_column].dropna().unique()) - valid_ids
    if invalid_ids:
        issues.append({
            "check": "foreign_key",
            "table": table_name,
            "status": "FAIL",
            "detail": f"{len(invalid_ids)} invalid {fk_column} values (e.g., {list(invalid_ids)[:5]})",
        })
    else:
        issues.append({
            "check": "foreign_key",
            "table": table_name,
            "status": "PASS",
            "detail": f"All {fk_column} values reference valid {ref_column}",
        })
    return issues


def check_duplicates(df: pd.DataFrame, table_name: str) -> List[dict]:
    issues = []
    if "visit_id" in df.columns:
        dup = df.duplicated(subset=["visit_id"]).sum()
    elif "claim_id" in df.columns:
        dup = df.duplicated(subset=["claim_id"]).sum()
    elif "client_id" in df.columns:
        dup = df.duplicated(subset=["client_id"]).sum()
    elif "worker_id" in df.columns:
        dup = df.duplicated(subset=["worker_id"]).sum()
    elif "exception_id" in df.columns:
        dup = df.duplicated(subset=["exception_id"]).sum()
    elif "allocation_id" in df.columns:
        dup = df.duplicated(subset=["allocation_id"]).sum()
    elif "funder_id" in df.columns:
        dup = df.duplicated(subset=["funder_id"]).sum()
    else:
        dup = df.duplicated().sum()
    if dup > 0:
        issues.append({
            "check": "duplicates",
            "table": table_name,
            "status": "FAIL",
            "detail": f"{dup} duplicate records found",
        })
    else:
        issues.append({
            "check": "duplicates",
            "table": table_name,
            "status": "PASS",
            "detail": "No duplicate records found",
        })
    return issues


def run_all_checks(data: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    all_issues = []

    all_issues.extend(check_required_columns(data["clients"], "clients"))
    all_issues.extend(check_required_columns(data["workers"], "workers"))
    all_issues.extend(check_required_columns(data["funders"], "funders"))
    all_issues.extend(check_required_columns(data["funding_allocations"], "funding_allocations"))
    all_issues.extend(check_required_columns(data["service_visits"], "service_visits"))
    all_issues.extend(check_required_columns(data["claims"], "claims"))
    all_issues.extend(check_required_columns(data["reconciliation_exceptions"], "reconciliation_exceptions"))

    all_issues.extend(check_nulls_in_required(data["clients"], "clients"))
    all_issues.extend(check_nulls_in_required(data["workers"], "workers"))
    all_issues.extend(check_nulls_in_required(data["funders"], "funders"))
    all_issues.extend(check_nulls_in_required(data["funding_allocations"], "funding_allocations"))
    all_issues.extend(check_nulls_in_required(data["service_visits"], "service_visits",
        ["visit_id", "client_id", "worker_id", "service_date", "scheduled_hours"]))
    all_issues.extend(check_nulls_in_required(data["claims"], "claims",
        ["claim_id", "visit_id", "client_id", "funder_id", "claim_date"]))
    all_issues.extend(check_nulls_in_required(data["reconciliation_exceptions"], "reconciliation_exceptions",
        ["exception_id", "claim_id", "exception_type", "detected_date"]))

    all_issues.extend(check_unique_ids(data["clients"], "client_id", "clients"))
    all_issues.extend(check_unique_ids(data["workers"], "worker_id", "workers"))
    all_issues.extend(check_unique_ids(data["funders"], "funder_id", "funders"))
    all_issues.extend(check_unique_ids(data["funding_allocations"], "allocation_id", "funding_allocations"))
    all_issues.extend(check_unique_ids(data["service_visits"], "visit_id", "service_visits"))
    all_issues.extend(check_unique_ids(data["claims"], "claim_id", "claims"))
    all_issues.extend(check_unique_ids(data["reconciliation_exceptions"], "exception_id", "reconciliation_exceptions"))

    all_issues.extend(check_date_parsable(data["clients"], ["intake_date"], "clients"))
    all_issues.extend(check_date_parsable(data["workers"], ["hire_date"], "workers"))
    all_issues.extend(check_date_parsable(data["funding_allocations"], ["allocation_start_date", "allocation_end_date"], "funding_allocations"))
    all_issues.extend(check_date_parsable(data["service_visits"], ["service_date"], "service_visits"))
    all_issues.extend(check_date_parsable(data["claims"], ["claim_date"], "claims"))
    all_issues.extend(check_date_parsable(data["reconciliation_exceptions"], ["detected_date"], "reconciliation_exceptions"))

    all_issues.extend(check_non_negative(data["clients"], ["active_flag"], "clients"))
    all_issues.extend(check_non_negative(data["workers"], ["weekly_capacity_hours"], "workers"))
    all_issues.extend(check_non_negative(data["funding_allocations"], ["allocated_amount", "approved_hours"], "funding_allocations"))
    all_issues.extend(check_non_negative(data["service_visits"], ["scheduled_hours", "completed_hours", "hourly_rate"], "service_visits"))
    all_issues.extend(check_non_negative(data["claims"], ["claim_amount"], "claims"))
    all_issues.extend(check_non_negative(data["reconciliation_exceptions"], ["exception_amount"], "reconciliation_exceptions"))

    all_issues.extend(check_completed_hours_tolerance(data["service_visits"]))

    all_issues.extend(check_foreign_keys(data["funding_allocations"], "client_id", data["clients"], "client_id", "funding_allocations"))
    all_issues.extend(check_foreign_keys(data["funding_allocations"], "funder_id", data["funders"], "funder_id", "funding_allocations"))
    all_issues.extend(check_foreign_keys(data["service_visits"], "client_id", data["clients"], "client_id", "service_visits"))
    all_issues.extend(check_foreign_keys(data["service_visits"], "worker_id", data["workers"], "worker_id", "service_visits"))
    all_issues.extend(check_foreign_keys(data["claims"], "visit_id", data["service_visits"], "visit_id", "claims"))
    all_issues.extend(check_foreign_keys(data["claims"], "client_id", data["clients"], "client_id", "claims"))
    all_issues.extend(check_foreign_keys(data["claims"], "funder_id", data["funders"], "funder_id", "claims"))
    all_issues.extend(check_foreign_keys(data["reconciliation_exceptions"], "claim_id", data["claims"], "claim_id", "reconciliation_exceptions"))

    all_issues.extend(check_duplicates(data["clients"], "clients"))
    all_issues.extend(check_duplicates(data["workers"], "workers"))
    all_issues.extend(check_duplicates(data["funders"], "funders"))
    all_issues.extend(check_duplicates(data["funding_allocations"], "funding_allocations"))
    all_issues.extend(check_duplicates(data["service_visits"], "service_visits"))
    all_issues.extend(check_duplicates(data["claims"], "claims"))
    all_issues.extend(check_duplicates(data["reconciliation_exceptions"], "reconciliation_exceptions"))

    report_df = pd.DataFrame(all_issues)
    report_path = os.path.join(config.processed_dir, "quality_report.csv")
    os.makedirs(config.processed_dir, exist_ok=True)
    report_df.to_csv(report_path, index=False)
    logger.info(f"Quality report saved to {report_path}")
    logger.info(f"Total checks: {len(report_df)}, PASS: {(report_df['status']=='PASS').sum()}, WARN: {(report_df['status']=='WARN').sum()}, FAIL: {(report_df['status']=='FAIL').sum()}")

    return report_df
