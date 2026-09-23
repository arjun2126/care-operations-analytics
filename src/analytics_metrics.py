import pandas as pd
from typing import Tuple, Optional, Dict, Any


def calculate_executive_kpis(
    claims: pd.DataFrame,
    visits: pd.DataFrame,
    exceptions: pd.DataFrame,
    funding_alloc: pd.DataFrame,
) -> Dict[str, Any]:
    total_visits = len(visits)
    completed_visits = len(visits[visits["visit_status"] == "Completed"])
    completed_hours = float(visits["completed_hours"].sum())
    total_claim_dollars = float(claims["claim_amount"].sum())
    approved_claim_dollars = float(claims[claims["claim_status"] == "Approved"]["claim_amount"].sum())
    approval_rate = (
        round(approved_claim_dollars / total_claim_dollars * 100, 1) if total_claim_dollars > 0 else 0.0
    )
    open_exceptions = len(exceptions[exceptions["exception_status"] != "Resolved"])
    open_exception_exposure = float(
        exceptions[exceptions["exception_status"] != "Resolved"]["exception_amount"].sum()
    )
    at_risk_count = int((funding_alloc["utilization_pct"] >= 90).sum()) if "utilization_pct" in funding_alloc.columns else 0

    return {
        "total_visits": int(total_visits),
        "completed_visits": int(completed_visits),
        "completed_hours": round(completed_hours, 1),
        "total_claim_dollars": round(total_claim_dollars, 2),
        "approved_claim_dollars": round(approved_claim_dollars, 2),
        "approval_rate": approval_rate,
        "open_exceptions": open_exceptions,
        "open_exception_exposure": round(open_exception_exposure, 2),
        "funding_at_risk_count": at_risk_count,
    }


def calculate_monthly_trends(
    visits: pd.DataFrame,
    claims: pd.DataFrame,
    exceptions: pd.DataFrame,
) -> pd.DataFrame:
    visits_monthly = visits.copy()
    visits_monthly["service_date"] = pd.to_datetime(visits_monthly["service_date"], errors="coerce")
    visits_monthly = visits_monthly.dropna(subset=["service_date"])
    visits_monthly["month"] = visits_monthly["service_date"].dt.to_period("M")

    monthly_visits = visits_monthly.groupby("month").agg(
        total_visits=("visit_id", "count"),
        completed_hours=("completed_hours", "sum"),
    ).reset_index()
    monthly_visits["month_label"] = monthly_visits["month"].astype(str)

    claims_monthly = claims.copy()
    claims_monthly["claim_date"] = pd.to_datetime(claims_monthly["claim_date"], errors="coerce")
    claims_monthly = claims_monthly.dropna(subset=["claim_date"])
    claims_monthly["month"] = claims_monthly["claim_date"].dt.to_period("M")

    monthly_claims = claims_monthly.groupby("month").agg(
        claim_dollars=("claim_amount", "sum"),
        total_claims=("claim_id", "count"),
        approved_dollars=pd.NamedAgg(column="claim_amount", aggfunc=lambda x: x[claims_monthly.loc[x.index, "claim_status"] == "Approved"].sum()),
    ).reset_index()
    monthly_claims["month_label"] = monthly_claims["month"].astype(str)
    monthly_claims["approval_rate"] = (
        monthly_claims["approved_dollars"] / monthly_claims["claim_dollars"].replace(0, pd.NA) * 100
    ).fillna(0).round(1)

    exceptions_monthly = exceptions.copy()
    exceptions_monthly["detected_date"] = pd.to_datetime(exceptions_monthly["detected_date"], errors="coerce")
    exceptions_monthly = exceptions_monthly.dropna(subset=["detected_date"])
    exceptions_monthly["month"] = exceptions_monthly["detected_date"].dt.to_period("M")

    monthly_exceptions = exceptions_monthly.groupby("month").agg(
        exception_count=("exception_id", "count"),
        exception_amount=("exception_amount", "sum"),
    ).reset_index()
    monthly_exceptions["month_label"] = monthly_exceptions["month"].astype(str)

    if "documentation_delay_days" in visits_monthly.columns:
        doc_delays = visits_monthly[visits_monthly["documentation_delay_days"].notna() & (visits_monthly["documentation_delay_days"] > 0)]
        if not doc_delays.empty:
            monthly_doc_delays = doc_delays.groupby("month").agg(
                doc_delay_count=("visit_id", "count"),
            ).reset_index()
        else:
            monthly_doc_delays = pd.DataFrame(columns=["month", "doc_delay_count"])
    else:
        monthly_doc_delays = pd.DataFrame(columns=["month"])
    monthly_doc_delays["month_label"] = monthly_doc_delays["month"].astype(str)
    monthly_doc_delays["doc_delay_rate"] = 0.0

    result = monthly_visits[["month_label", "total_visits", "completed_hours"]].merge(
        monthly_claims[["month_label", "claim_dollars", "approval_rate"]], on="month_label", how="outer"
    ).merge(
        monthly_exceptions[["month_label", "exception_count", "exception_amount"]], on="month_label", how="outer"
    ).merge(
        monthly_doc_delays[["month_label", "doc_delay_rate"]], on="month_label", how="outer"
    ).fillna(0)

    result = result.sort_values("month_label").reset_index(drop=True)
    return result


def calculate_funding_utilization(funding_alloc: pd.DataFrame) -> pd.DataFrame:
    if funding_alloc.empty:
        return funding_alloc
    result = funding_alloc.copy()
    result = result.sort_values("utilization_pct", ascending=False)
    return result


def calculate_at_risk_funding(funding_alloc: pd.DataFrame) -> pd.DataFrame:
    if "utilization_pct" not in funding_alloc.columns:
        return pd.DataFrame()
    return funding_alloc[funding_alloc["utilization_pct"] >= 90].copy()


def calculate_worker_capacity(visits: pd.DataFrame, workers: pd.DataFrame) -> pd.DataFrame:
    if visits.empty or workers.empty:
        return pd.DataFrame()
    visits_copy = visits.copy()
    visits_copy["service_date"] = pd.to_datetime(visits_copy["service_date"], errors="coerce")
    visits_copy = visits_copy.dropna(subset=["service_date"])
    visits_copy["week_start"] = visits_copy["service_date"].dt.to_period("W").apply(lambda p: p.start_time)

    weekly = visits_copy[visits_copy["visit_status"] == "Completed"].groupby(["worker_id", "week_start"]).agg(
        weekly_completed_hours=("completed_hours", "sum"),
    ).reset_index()

    result = weekly.merge(workers[["worker_id", "worker_name", "worker_type", "weekly_capacity_hours"]], on="worker_id", how="left")
    result["capacity_utilization_pct"] = (result["weekly_completed_hours"] / result["weekly_capacity_hours"].replace(0, pd.NA) * 100).fillna(0).round(1)
    result["exceeding_capacity"] = result["weekly_completed_hours"] > result["weekly_capacity_hours"]
    return result[result["exceeding_capacity"]].sort_values("weekly_completed_hours", ascending=False)


def calculate_doc_delay_analysis(visits: pd.DataFrame) -> pd.DataFrame:
    if visits.empty:
        return pd.DataFrame()
    visits_copy = visits.copy()
    visits_copy["service_date"] = pd.to_datetime(visits_copy["service_date"], errors="coerce")
    visits_copy = visits_copy.dropna(subset=["service_date"])
    visits_copy["month"] = visits_copy["service_date"].dt.to_period("M").astype(str)
    delays = visits_copy[visits_copy["documentation_delay_days"].notna() & (visits_copy["documentation_delay_days"] > 0)]
    monthly = delays.groupby("month").agg(
        delay_count=("visit_id", "count"),
        avg_delay_days=("documentation_delay_days", "mean"),
    ).reset_index()
    return monthly.sort_values("month")


def calculate_exception_aging(exceptions: pd.DataFrame) -> pd.DataFrame:
    if exceptions.empty:
        return pd.DataFrame()
    ex = exceptions.copy()
    ex["detected_date"] = pd.to_datetime(ex["detected_date"], errors="coerce")
    ex["resolved_date"] = pd.to_datetime(ex["resolved_date"], errors="coerce")
    ex = ex.dropna(subset=["detected_date"])
    ex["days_open"] = ex.apply(
        lambda r: (pd.Timestamp.now() - r["detected_date"]).days if pd.isna(r["resolved_date"]) else (r["resolved_date"] - r["detected_date"]).days,
        axis=1,
    )
    return ex.sort_values("days_open", ascending=False)


def calculate_rejection_rates(claims: pd.DataFrame) -> pd.DataFrame:
    if claims.empty:
        return pd.DataFrame()
    rejected = claims[claims["claim_status"] == "Rejected"].copy()
    if rejected.empty:
        return pd.DataFrame()
    result = rejected.groupby(["funder_id", "rejection_reason"]).agg(
        rejection_count=("claim_id", "count"),
        rejected_amount=("claim_amount", "sum"),
    ).reset_index()
    return result.sort_values("rejection_count", ascending=False)


def calculate_duplicate_risk(claims: pd.DataFrame) -> pd.DataFrame:
    if claims.empty:
        return pd.DataFrame()
    duplicates = claims[claims["duplicate_candidate_flag"] == True].copy()
    if duplicates.empty:
        return pd.DataFrame()
    result = duplicates.groupby("funder_id").agg(
        duplicate_count=("claim_id", "count"),
        duplicate_exposure=("claim_amount", "sum"),
    ).reset_index()
    return result.sort_values("duplicate_exposure", ascending=False)


def generate_narrative_observations(kpis: dict, monthly_trends: pd.DataFrame, at_risk: pd.DataFrame, exceptions_aging: pd.DataFrame) -> list[str]:
    observations = []

    if not kpis or "approval_rate" not in kpis:
        return observations

    if kpis["approval_rate"] < 60:
        observations.append(
            f"Claim approval rate is {kpis['approval_rate']}%, below 60%. "
            f"This suggests significant revenue cycle friction requiring attention."
        )
    elif kpis["approval_rate"] >= 80:
        observations.append(
            f"Claim approval rate is {kpis['approval_rate']}%, indicating healthy revenue cycle performance."
        )
    else:
        observations.append(
            f"Claim approval rate is {kpis['approval_rate']}%, within moderate range but with room for improvement."
        )

    if kpis["funding_at_risk_count"] > 0:
        observations.append(
            f"{kpis['funding_at_risk_count']} client-funder allocations are at or above 90% utilization, "
            f"posing budget overrun risk."
        )
    else:
        observations.append(
            "No allocations currently exceed 90% utilization threshold."
        )

    if kpis["open_exceptions"] > 0:
        observations.append(
            f"{kpis['open_exceptions']} reconciliation exceptions remain open with "
            f"C${kpis['open_exception_exposure']:,.2f} in exposure."
        )

    high_priority = exceptions_aging[exceptions_aging["priority"] == "High"] if not exceptions_aging.empty else pd.DataFrame()
    if len(high_priority) > 0:
        observations.append(
            f"{len(high_priority)} high-priority exceptions remain unresolved, "
            f"requiring immediate analyst attention."
        )

    return observations[:4] if len(observations) > 4 else observations