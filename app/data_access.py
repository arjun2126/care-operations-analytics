import os
from pathlib import Path
import pandas as pd


def _find_project_root() -> Path:
    current = Path(__file__).resolve().parent
    for candidate in [current, *current.parents]:
        if (candidate / "data" / "processed").is_dir():
            return candidate
    return current.parent


PROJECT_ROOT = _find_project_root()
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
RAW_DIR = PROJECT_ROOT / "data" / "raw"


def _require_processed_files() -> None:
    required = ["clients.csv", "claims.csv", "funders.csv", "funding_allocations.csv",
                "service_visits.csv", "reconciliation_exceptions.csv", "workers.csv"]
    missing = [f for f in required if not (PROCESSED_DIR / f).is_file()]
    if missing:
        raise FileNotFoundError(
            f"Missing processed data files: {missing}\n"
            f"Run the pipeline to regenerate them:\n"
            f"  python -m src.pipeline"
        )


def load_processed_data() -> dict[str, pd.DataFrame]:
    _require_processed_files()
    data = {}
    for name in ["clients", "workers", "funders", "funding_allocations",
                 "service_visits", "claims", "reconciliation_exceptions"]:
        path = PROCESSED_DIR / f"{name}.csv"
        if path.is_file():
            data[name] = pd.read_csv(path)
    return data


def load_dashboard_data() -> dict[str, pd.DataFrame]:
    data = load_processed_data()
    data["claims_with_exceptions"] = data["reconciliation_exceptions"][["claim_id"]].drop_duplicates()
    return data


def get_data_source_status() -> dict:
    required = ["clients", "workers", "funders", "funding_allocations",
                "service_visits", "claims", "reconciliation_exceptions"]
    statuses = {}
    for name in required:
        path = PROCESSED_DIR / f"{name}.csv"
        if path.is_file():
            df = pd.read_csv(path)
            statuses[name] = {"status": "loaded", "rows": len(df), "source": str(path)}
        else:
            statuses[name] = {"status": "missing", "rows": 0, "source": str(path)}
    all_loaded = all(s["status"] == "loaded" for s in statuses.values())
    return {"all_loaded": all_loaded, "tables": statuses}


def load_claims_with_details() -> pd.DataFrame:
    data = load_dashboard_data()
    claims = data["claims"].copy()
    visits = data["service_visits"][["visit_id", "service_type", "completed_hours", "scheduled_hours", "hourly_rate"]].copy()
    clients = data["clients"][["client_id", "city", "service_program"]].copy()
    funders = data["funders"][["funder_id", "funder_name", "funding_type"]].copy()

    claims = claims.merge(visits, on="visit_id", how="left")
    claims = claims.merge(clients, on="client_id", how="left")
    claims = claims.merge(funders, on="funder_id", how="left")
    return claims


def load_claims_risk_features() -> pd.DataFrame:
    claims = load_claims_with_details()
    claims["hours_variance"] = claims["completed_hours"] - claims["scheduled_hours"]
    claims["hours_variance_pct"] = (claims["hours_variance"] / claims["scheduled_hours"].replace(0, pd.NA)).fillna(0)
    return claims


def load_funding_with_claims() -> pd.DataFrame:
    data = load_dashboard_data()
    alloc = data["funding_allocations"].copy()
    claims = data["claims"].copy()
    approved = claims[claims["claim_status"] == "Approved"].groupby(["client_id", "funder_id"])["claim_amount"].sum().reset_index()
    approved.columns = ["client_id", "funder_id", "total_approved_spend"]
    alloc = alloc.merge(approved, on=["client_id", "funder_id"], how="left")
    alloc["total_approved_spend"] = alloc["total_approved_spend"].fillna(0)
    alloc["remaining_funding"] = alloc["allocated_amount"] - alloc["total_approved_spend"]
    alloc["utilization_pct"] = (alloc["total_approved_spend"] / alloc["allocated_amount"].replace(0, pd.NA) * 100).fillna(0)
    alloc["at_risk"] = alloc["utilization_pct"] >= 90
    return alloc


def load_exceptions_with_claims() -> pd.DataFrame:
    data = load_dashboard_data()
    exceptions = data["reconciliation_exceptions"].copy()
    claims = data["claims"][["claim_id", "claim_amount", "claim_status", "client_id", "funder_id"]].copy()
    exceptions = exceptions.merge(claims, on="claim_id", how="left")
    return exceptions