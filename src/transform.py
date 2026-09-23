import os
import logging

import pandas as pd

from src.config import config

logger = logging.getLogger(__name__)


def clean_clients(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    valid_mask = df["client_id"].notna() & df["client_name"].notna()
    valid = df[valid_mask].copy().reset_index(drop=True)
    invalid = df[~valid_mask].copy().reset_index(drop=True)
    if not invalid.empty:
        logger.info(f"Clients: {len(invalid)} rejected records")
    return valid, invalid


def clean_workers(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    valid_mask = df["worker_id"].notna() & df["worker_name"].notna()
    valid = df[valid_mask].copy().reset_index(drop=True)
    invalid = df[~valid_mask].copy().reset_index(drop=True)
    return valid, invalid


def clean_service_visits(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    valid_mask = (
        df["visit_id"].notna()
        & df["client_id"].notna()
        & df["worker_id"].notna()
        & df["service_date"].notna()
        & df["scheduled_hours"].notna()
        & (df["scheduled_hours"] >= 0)
    )
    valid = df[valid_mask].copy().reset_index(drop=True)
    invalid = df[~valid_mask].copy().reset_index(drop=True)
    logger.info(f"Service visits: {len(invalid)} rejected records")
    return valid, invalid


def clean_claims(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    valid_mask = (
        df["claim_id"].notna()
        & df["visit_id"].notna()
        & df["claim_date"].notna()
        & df["claim_amount"].notna()
        & (df["claim_amount"] >= 0)
    )
    valid = df[valid_mask].copy().reset_index(drop=True)
    invalid = df[~valid_mask].copy().reset_index(drop=True)
    return valid, invalid


def clean_funding_allocations(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    valid_mask = (
        df["allocation_id"].notna()
        & df["client_id"].notna()
        & df["funder_id"].notna()
        & df["allocated_amount"].notna()
        & (df["allocated_amount"] >= 0)
    )
    valid = df[valid_mask].copy().reset_index(drop=True)
    invalid = df[~valid_mask].copy().reset_index(drop=True)
    return valid, invalid


def clean_reconciliation_exceptions(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    valid_mask = (
        df["exception_id"].notna()
        & df["claim_id"].notna()
        & df["exception_type"].notna()
        & df["detected_date"].notna()
        & df["exception_amount"].notna()
        & (df["exception_amount"] >= 0)
    )
    valid = df[valid_mask].copy().reset_index(drop=True)
    invalid = df[~valid_mask].copy().reset_index(drop=True)
    return valid, invalid


def clean_funders(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    valid_mask = df["funder_id"].notna() & df["funder_name"].notna()
    valid = df[valid_mask].copy().reset_index(drop=True)
    invalid = df[~valid_mask].copy().reset_index(drop=True)
    return valid, invalid


def apply_all_cleaning(data: dict) -> tuple[dict, dict]:
    cleaners = {
        "clients": clean_clients,
        "workers": clean_workers,
        "funders": clean_funders,
        "funding_allocations": clean_funding_allocations,
        "service_visits": clean_service_visits,
        "claims": clean_claims,
        "reconciliation_exceptions": clean_reconciliation_exceptions,
    }
    cleaned = {}
    rejected = {}
    for name, cleaner in cleaners.items():
        if name in data:
            c, r = cleaner(data[name])
            cleaned[name] = c
            rejected[name] = r
    return cleaned, rejected


def save_processed_data(cleaned: dict, rejected: dict, output_dir: str = None) -> None:
    if output_dir is None:
        output_dir = config.processed_dir
    os.makedirs(output_dir, exist_ok=True)
    for name, df in cleaned.items():
        path = os.path.join(output_dir, f"{name}.csv")
        df.to_csv(path, index=False)
    for name, df in rejected.items():
        if not df.empty:
            path = os.path.join(output_dir, f"{name}_rejected.csv")
            df.to_csv(path, index=False)
    quality_log = []
    for name, df in cleaned.items():
        quality_log.append({"table": name, "valid_rows": len(df)})
    for name, df in rejected.items():
        if not df.empty:
            quality_log.append({"table": f"{name}_rejected", "rejected_rows": len(df)})
    pd.DataFrame(quality_log).to_csv(
        os.path.join(output_dir, "loading_summary.csv"), index=False
    )
    logger.info(
        f"Saved {sum(len(v) for v in cleaned.values())} valid records and "
        f"{sum(len(v) for v in rejected.values())} rejected records"
    )