import pandas as pd
import numpy as np
from typing import Tuple, Optional


def build_risk_features(claims: pd.DataFrame) -> pd.DataFrame:
    df = claims.copy()

    df["hours_variance"] = df["completed_hours"] - df["scheduled_hours"]
    df["hours_variance_pct"] = (
        (df["hours_variance"] / df["scheduled_hours"].replace(0, np.nan)) * 100
    ).fillna(0)
    df["hours_variance_pct"] = df["hours_variance_pct"].fillna(0)

    df["has_late_submission"] = df["submitted_late_flag"].astype(int) if "submitted_late_flag" in df.columns else 0
    df["has_duplicate_flag"] = df["duplicate_candidate_flag"].astype(int) if "duplicate_candidate_flag" in df.columns else 0
    df["doc_delay_days"] = df["documentation_delay_days"].fillna(0).astype(int) if "documentation_delay_days" in df.columns else 0

    df["log_claim_amount"] = np.log1p(df["claim_amount"])
    df["claim_amount_per_hour"] = df.apply(
        lambda r: r["claim_amount"] / r["completed_hours"] if r["completed_hours"] > 0 else 0, axis=1
    )
    df["claim_amount_per_hour"] = df["claim_amount_per_hour"].fillna(0)

    df["funding_type"] = df["funding_type"].fillna("Unknown")
    df["service_type"] = df["service_type"].fillna("Unknown")

    df["is_high_risk_target"] = (
        (df["claim_status"] == "Rejected")
        | (df["duplicate_candidate_flag"] == True)
    ).astype(int)

    return df


def get_risk_feature_columns() -> list[str]:
    return [
        "log_claim_amount",
        "claim_amount_per_hour",
        "hours_variance_pct",
        "has_late_submission",
        "has_duplicate_flag",
        "doc_delay_days",
    ]


def encode_categorical_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    funding_dummies = pd.get_dummies(df["funding_type"], prefix="funding", drop_first=True)
    service_dummies = pd.get_dummies(df["service_type"], prefix="service", drop_first=True)
    df = pd.concat([df, funding_dummies, service_dummies], axis=1)
    return df