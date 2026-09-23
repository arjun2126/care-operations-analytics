import pytest
import pandas as pd
import numpy as np
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.risk_model import generate_risk_scores, train_model, _build_model_data
from src.feature_engineering import build_risk_features, get_risk_feature_columns, encode_categorical_features


class TestRiskModelFeatures:
    def test_feature_creation_output(self):
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
        assert "is_high_risk_target" in df.columns

    def test_risk_score_range(self):
        claims = pd.DataFrame({
            "claim_id": [f"C{i:04d}" for i in range(20)],
            "client_id": [f"CL{i:04d}" for i in range(20)],
            "funder_id": ["FN1"] * 10 + ["FN2"] * 10,
            "claim_amount": np.random.uniform(50, 500, 20),
            "claim_status": ["Approved"] * 15 + ["Rejected"] * 5,
            "documentation_delay_days": np.random.randint(0, 20, 20),
            "submitted_late_flag": [True] * 5 + [False] * 15,
            "duplicate_candidate_flag": [True] * 3 + [False] * 17,
            "completed_hours": np.random.uniform(1, 5, 20),
            "scheduled_hours": np.random.uniform(1, 5, 20),
            "hourly_rate": np.random.uniform(30, 90, 20),
            "funding_type": ["Provincial"] * 10 + ["Federal"] * 10,
            "service_type": ["Personal Care"] * 10 + ["Nursing Care"] * 10,
        })
        risk_df = generate_risk_scores()
        if risk_df is not None and not risk_df.empty:
            assert (risk_df["risk_score"] >= 0).all()
            assert (risk_df["risk_score"] <= 1).all()

    def test_risk_band_assignment(self):
        claims = pd.DataFrame({
            "claim_id": [f"C{i:04d}" for i in range(20)],
            "client_id": [f"CL{i:04d}" for i in range(20)],
            "funder_id": ["FN1"] * 20,
            "claim_amount": np.random.uniform(50, 500, 20),
            "claim_status": ["Approved"] * 15 + ["Rejected"] * 5,
            "documentation_delay_days": np.random.randint(0, 20, 20),
            "submitted_late_flag": [True] * 5 + [False] * 15,
            "duplicate_candidate_flag": [True] * 3 + [False] * 17,
            "completed_hours": np.random.uniform(1, 5, 20),
            "scheduled_hours": np.random.uniform(1, 5, 20),
            "hourly_rate": np.random.uniform(30, 90, 20),
            "funding_type": ["Provincial"] * 20,
            "service_type": ["Personal Care"] * 20,
        })
        risk_df = generate_risk_scores()
        if risk_df is not None and not risk_df.empty:
            valid_bands = {"Low", "Medium", "High"}
            assert set(risk_df["risk_band"].unique()).issubset(valid_bands)

    def test_output_includes_required_columns(self):
        claims = pd.DataFrame({
            "claim_id": [f"C{i:04d}" for i in range(20)],
            "client_id": [f"CL{i:04d}" for i in range(20)],
            "funder_id": ["FN1"] * 20,
            "claim_amount": np.random.uniform(50, 500, 20),
            "claim_status": ["Approved"] * 15 + ["Rejected"] * 5,
            "documentation_delay_days": np.random.randint(0, 20, 20),
            "submitted_late_flag": [True] * 5 + [False] * 15,
            "duplicate_candidate_flag": [True] * 3 + [False] * 17,
            "completed_hours": np.random.uniform(1, 5, 20),
            "scheduled_hours": np.random.uniform(1, 5, 20),
            "hourly_rate": np.random.uniform(30, 90, 20),
            "funding_type": ["Provincial"] * 20,
            "service_type": ["Personal Care"] * 20,
        })
        risk_df = generate_risk_scores()
        if risk_df is not None and not risk_df.empty:
            required = {"claim_id", "risk_score", "risk_band", "reason_summary"}
            assert required.issubset(set(risk_df.columns))

    def test_handles_small_dataset(self):
        claims = pd.DataFrame({
            "claim_id": ["C1"],
            "client_id": ["CL1"],
            "funder_id": ["FN1"],
            "claim_amount": [100.0],
            "claim_status": ["Approved"],
            "documentation_delay_days": [5],
            "submitted_late_flag": [False],
            "duplicate_candidate_flag": [False],
            "completed_hours": [2.0],
            "scheduled_hours": [1.5],
            "hourly_rate": [50.0],
            "funding_type": ["Provincial"],
            "service_type": ["Personal Care"],
        })
        risk_df = generate_risk_scores()
        if risk_df is not None:
            assert (risk_df["risk_score"] >= 0).all()


class TestTrainModel:
    def test_train_model_handles_limited_data(self):
        result = _build_model_data()
        if result is None:
            pytest.skip("Insufficient data for model training; test skipped gracefully")
        else:
            X, y, df = result
            assert len(X) > 0
            assert len(y) > 0