import pytest
import pandas as pd
import numpy as np
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.analytics_metrics import calculate_executive_kpis, calculate_monthly_trends, calculate_funding_utilization, calculate_at_risk_funding, calculate_exception_aging, calculate_rejection_rates, calculate_duplicate_risk, generate_narrative_observations


class TestExecutiveKPIs:
    def test_calculates_all_kpis(self):
        claims = pd.DataFrame({
            "claim_id": ["C1", "C2", "C3"],
            "claim_amount": [100.0, 200.0, 300.0],
            "claim_status": ["Approved", "Rejected", "Approved"],
        })
        visits = pd.DataFrame({
            "visit_id": ["V1", "V2"],
            "visit_status": ["Completed", "Cancelled"],
            "completed_hours": [2.0, 0.0],
        })
        exceptions = pd.DataFrame({
            "exception_id": ["E1"],
            "exception_status": ["Open"],
            "exception_amount": [500.0],
        })
        funding = pd.DataFrame({"utilization_pct": [95.0, 50.0]})
        
        kpis = calculate_executive_kpis(claims, visits, exceptions, funding)
        assert kpis["total_visits"] == 2
        assert kpis["completed_hours"] == 2.0
        assert kpis["total_claim_dollars"] == 600.0
        assert kpis["approval_rate"] == 66.7
        assert kpis["open_exceptions"] == 1
        assert kpis["funding_at_risk_count"] == 1

    def test_empty_data_handling(self):
        claims = pd.DataFrame(columns=["claim_id", "claim_amount", "claim_status"])
        visits = pd.DataFrame(columns=["visit_id", "visit_status", "completed_hours"])
        exceptions = pd.DataFrame(columns=["exception_id", "exception_status", "exception_amount"])
        funding = pd.DataFrame(columns=["utilization_pct"])
        
        kpis = calculate_executive_kpis(claims, visits, exceptions, funding)
        assert kpis["total_visits"] == 0
        assert kpis["approval_rate"] == 0.0


class TestFundingUtilization:
    def test_utilization_calculation(self):
        funding = pd.DataFrame({
            "allocation_id": ["A1", "A2"],
            "client_id": ["CL1", "CL2"],
            "funder_id": ["FN1", "FN2"],
            "allocated_amount": [1000.0, 2000.0],
            "total_approved_spend": [950.0, 500.0],
            "utilization_pct": [95.0, 25.0],
            "at_risk": [True, False],
        })
        at_risk = calculate_at_risk_funding(funding)
        assert len(at_risk) == 1
        assert at_risk.iloc[0]["utilization_pct"] == 95.0

    def test_empty_funding(self):
        funding = pd.DataFrame(columns=["utilization_pct"])
        result = calculate_at_risk_funding(funding)
        assert result.empty


class TestExceptionAging:
    def test_days_open_calculation(self):
        exceptions = pd.DataFrame({
            "exception_id": ["E1", "E2"],
            "detected_date": pd.to_datetime(["2024-01-01", "2024-06-01"]),
            "resolved_date": [pd.NaT, pd.Timestamp("2024-07-01")],
            "exception_status": ["Open", "Resolved"],
            "exception_amount": [1000.0, 500.0],
            "priority": ["High", "Medium"],
        })
        aging = calculate_exception_aging(exceptions)
        assert "days_open" in aging.columns
        assert aging.shape[0] == 2


class TestNarrativeObservations:
    def test_returns_list(self):
        kpis = {"approval_rate": 50.0, "open_exceptions": 5, "funding_at_risk_count": 2, "open_exception_exposure": 1000.0}
        monthly = pd.DataFrame()
        at_risk = pd.DataFrame()
        exceptions_aging = pd.DataFrame({"priority": ["High"]})
        
        observations = generate_narrative_observations(kpis, monthly, at_risk, exceptions_aging)
        assert isinstance(observations, list)
        assert len(observations) <= 4

    def test_empty_data(self):
        observations = generate_narrative_observations({}, pd.DataFrame(), pd.DataFrame(), pd.DataFrame())
        assert isinstance(observations, list)


class TestMonthlyTrends:
    def test_calculates_monthly(self):
        visits = pd.DataFrame({
            "visit_id": ["V1", "V2", "V3"],
            "service_date": pd.to_datetime(["2024-01-15", "2024-01-20", "2024-02-10"]),
            "visit_status": ["Completed", "Completed", "Cancelled"],
            "completed_hours": [2.0, 3.0, 0.0],
        })
        claims = pd.DataFrame({
            "claim_id": ["C1", "C2"],
            "claim_date": pd.to_datetime(["2024-01-16", "2024-02-11"]),
            "claim_amount": [100.0, 200.0],
            "claim_status": ["Approved", "Rejected"],
        })
        exceptions = pd.DataFrame({
            "exception_id": ["E1"],
            "detected_date": pd.to_datetime(["2024-01-20"]),
            "exception_amount": [500.0],
        })
        
        trends = calculate_monthly_trends(visits, claims, exceptions)
        assert not trends.empty
        assert "month_label" in trends.columns


from src.risk_model import generate_risk_scores
from src.feature_engineering import build_risk_features, get_risk_feature_columns


class TestRiskModelFeatures:
    def test_build_risk_features_creates_columns(self):
        claims = pd.DataFrame({
            "claim_id": ["C1", "C2"],
            "client_id": ["CL1", "CL2"],
            "funder_id": ["FN1", "FN2"],
            "claim_amount": [100.0, 500.0],
            "claim_status": ["Approved", "Rejected"],
            "documentation_delay_days": [5, 0],
            "submitted_late_flag": [True, False],
            "duplicate_candidate_flag": [False, True],
            "completed_hours": [2.0, 3.0],
            "scheduled_hours": [1.5, 2.5],
            "hourly_rate": [50.0, 166.0],
            "funding_type": ["Provincial", "Federal"],
            "service_type": ["Personal Care", "Nursing Care"],
        })
        df = build_risk_features(claims)
        assert "hours_variance" in df.columns
        assert "risk_score" not in df.columns
        assert "is_high_risk_target" in df.columns

    def test_feature_columns_list(self):
        cols = get_risk_feature_columns()
        assert len(cols) >= 4
        assert "log_claim_amount" in cols
        assert "has_late_submission" in cols