import pytest
import pandas as pd
from src.quality_checks import (
    check_required_columns,
    check_nulls_in_required,
    check_non_negative,
    check_duplicates,
    check_foreign_keys,
)


def make_clients(n=10):
    return pd.DataFrame({
        "client_id": [f"CL{i:05d}" for i in range(1, n + 1)],
        "client_name": [f"Client {i}" for i in range(1, n + 1)],
        "city": ["Toronto"] * n,
        "service_program": ["Home Care"] * n,
        "intake_date": pd.to_datetime(["2024-01-01"] * n).date,
        "active_flag": [True] * n,
    })


def make_visits(n=10):
    return pd.DataFrame({
        "visit_id": [f"VS{i:07d}" for i in range(1, n + 1)],
        "client_id": [f"CL{i:05d}" for i in range(1, n + 1)],
        "worker_id": [f"WK{i:04d}" for i in range(1, n + 1)],
        "service_date": pd.to_datetime(["2024-01-01"] * n).date,
        "service_type": ["Personal Care"] * n,
        "scheduled_hours": [2.0] * n,
        "completed_hours": [2.0] * n,
        "hourly_rate": [50.0] * n,
        "visit_status": ["Completed"] * n,
        "documentation_submitted_date": pd.to_datetime(["2024-01-02"] * n).date,
        "documentation_delay_days": [1] * n,
    })


class TestRequiredColumns:
    def test_all_required_columns_present(self):
        df = make_clients()
        issues = check_required_columns(df, "clients")
        fail_issues = [i for i in issues if i["status"] == "FAIL"]
        assert len(fail_issues) == 0

    def test_missing_required_columns_detected(self):
        df = make_clients()[["client_id"]]
        issues = check_required_columns(df, "clients")
        fail_issues = [i for i in issues if i["status"] == "FAIL"]
        assert len(fail_issues) > 0
        assert "Missing columns" in fail_issues[0]["detail"]


class TestNegativeValues:
    def test_negative_hours_detected(self):
        df = make_visits()
        df.loc[0, "completed_hours"] = -1.0
        issues = check_non_negative(df, ["completed_hours"], "service_visits")
        warn_issues = [i for i in issues if i["status"] == "WARN"]
        assert len(warn_issues) > 0

    def test_negative_claim_amount_detected(self):
        claims = pd.DataFrame({
            "claim_id": ["CM000001"],
            "visit_id": ["VS0000001"],
            "client_id": ["CL00001"],
            "funder_id": ["FN001"],
            "claim_date": pd.to_datetime(["2024-01-01"]).date,
            "claim_amount": [-100.0],
            "claim_status": ["Approved"],
        })
        issues = check_non_negative(claims, ["claim_amount"], "claims")
        warn_issues = [i for i in issues if i["status"] == "WARN"]
        assert len(warn_issues) > 0

    def test_all_non_negative_passes(self):
        df = make_visits()
        issues = check_non_negative(df, ["scheduled_hours", "completed_hours", "hourly_rate"], "service_visits")
        warn_issues = [i for i in issues if i["status"] == "WARN"]
        assert len(warn_issues) == 0


class TestDuplicateDetection:
    def test_duplicates_detected(self):
        df = make_clients()
        df = pd.concat([df, df.iloc[[0]]], ignore_index=True)
        issues = check_duplicates(df, "clients")
        fail_issues = [i for i in issues if i["status"] == "FAIL"]
        assert len(fail_issues) > 0

    def test_no_duplicates_passes(self):
        df = make_clients()
        issues = check_duplicates(df, "clients")
        fail_issues = [i for i in issues if i["status"] == "FAIL"]
        assert len(fail_issues) == 0


class TestForeignKeyDetection:
    def test_invalid_foreign_key_detected(self):
        visits = make_visits()
        visits.loc[0, "client_id"] = "CL99999"
        clients = make_clients(5)
        issues = check_foreign_keys(visits, "client_id", clients, "client_id", "service_visits")
        fail_issues = [i for i in issues if i["status"] == "FAIL"]
        assert len(fail_issues) > 0

    def test_valid_foreign_keys_pass(self):
        visits = make_visits()
        clients = make_clients(10)
        issues = check_foreign_keys(visits, "client_id", clients, "client_id", "service_visits")
        fail_issues = [i for i in issues if i["status"] == "FAIL"]
        assert len(fail_issues) == 0


class TestTransformRules:
    def test_clean_service_visits_filters_invalid_records(self):
        from src.transform import clean_service_visits
        df = pd.DataFrame({
            "visit_id": ["VS0000001", "VS0000002", None],
            "client_id": ["CL00001", None, "CL00003"],
            "worker_id": ["WK0001", "WK0002", "WK0003"],
            "service_date": [pd.Timestamp("2024-01-01").date(), pd.Timestamp("2024-01-02").date(), None],
            "scheduled_hours": [2.0, -1.0, 1.5],
            "completed_hours": [2.0, 0.0, 1.5],
            "hourly_rate": [50.0, 50.0, 50.0],
            "visit_status": ["Completed", "Cancelled", "Completed"],
            "service_type": ["Personal Care", "Nursing", "Physio"],
            "documentation_submitted_date": [pd.Timestamp("2024-01-02").date(), None, pd.Timestamp("2024-01-03").date()],
            "documentation_delay_days": [1, None, 2],
        })
        valid, invalid = clean_service_visits(df)
        assert len(valid) == 1
        assert len(invalid) == 2
        assert valid.iloc[0]["visit_id"] == "VS0000001"

    def test_clean_clients_filters_null_names(self):
        from src.transform import clean_clients
        df = pd.DataFrame({
            "client_id": ["CL00001", None, "CL00003"],
            "client_name": ["Alice", None, "Charlie"],
            "city": ["Toronto", "Ottawa", None],
            "service_program": ["Home Care", "Nursing", "Physio"],
            "intake_date": [pd.Timestamp("2024-01-01").date(), pd.Timestamp("2024-01-02").date(), pd.Timestamp("2024-01-03").date()],
            "active_flag": [True, False, True],
        })
        valid, invalid = clean_clients(df)
        assert len(valid) == 2
        assert len(invalid) == 1
