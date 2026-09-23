import pandas as pd
import pytest
from src.transform import (
    clean_clients,
    clean_workers,
    clean_service_visits,
    clean_claims,
    clean_funding_allocations,
    clean_reconciliation_exceptions,
    apply_all_cleaning,
)


def make_clients():
    return pd.DataFrame({
        "client_id": [f"CL{i:05d}" for i in range(1, 6)],
        "client_name": [f"Client {i}" for i in range(1, 6)],
        "city": ["Toronto"] * 5,
        "service_program": ["Home Care"] * 5,
        "intake_date": pd.to_datetime(["2024-01-01"] * 5).date,
        "active_flag": [True] * 5,
    })


def make_workers():
    return pd.DataFrame({
        "worker_id": [f"WK{i:04d}" for i in range(1, 6)],
        "worker_name": [f"Worker {i}" for i in range(1, 6)],
        "worker_type": ["RN"] * 5,
        "home_city": ["Toronto"] * 5,
        "weekly_capacity_hours": [40.0] * 5,
        "hire_date": pd.to_datetime(["2023-01-01"] * 5).date,
        "active_flag": [True] * 5,
    })


def make_visits():
    return pd.DataFrame({
        "visit_id": [f"VS{i:07d}" for i in range(1, 6)],
        "client_id": [f"CL{i:05d}" for i in range(1, 6)],
        "worker_id": [f"WK{i:04d}" for i in range(1, 6)],
        "service_date": pd.to_datetime(["2024-01-01"] * 5).date,
        "service_type": ["Personal Care"] * 5,
        "scheduled_hours": [2.0] * 5,
        "completed_hours": [2.0] * 5,
        "hourly_rate": [50.0] * 5,
        "visit_status": ["Completed"] * 5,
        "documentation_submitted_date": pd.to_datetime(["2024-01-02"] * 5).date,
        "documentation_delay_days": [1] * 5,
    })


class TestCleanClients:
    def test_removes_null_client_id(self):
        df = make_clients()
        df.loc[0, "client_id"] = None
        valid, invalid = clean_clients(df)
        assert len(valid) == 4
        assert len(invalid) == 1

    def test_removes_null_client_name(self):
        df = make_clients()
        df.loc[0, "client_name"] = None
        valid, invalid = clean_clients(df)
        assert len(valid) == 4
        assert len(invalid) == 1

    def test_preserves_valid_records(self):
        df = make_clients()
        valid, _ = clean_clients(df)
        assert len(valid) == 5
        assert list(valid["client_name"]) == list(make_clients()["client_name"])


class TestCleanWorkers:
    def test_removes_null_worker_id(self):
        df = make_workers()
        df.loc[0, "worker_id"] = None
        valid, invalid = clean_workers(df)
        assert len(valid) == 4
        assert len(invalid) == 1


class TestCleanServiceVisits:
    def test_filters_visits_with_null_visit_id(self):
        df = make_visits()
        df.loc[0, "visit_id"] = None
        valid, invalid = clean_service_visits(df)
        assert len(valid) == 4

    def test_filters_visits_with_negative_scheduled_hours(self):
        df = make_visits()
        df.loc[0, "scheduled_hours"] = -1.0
        valid, invalid = clean_service_visits(df)
        assert len(valid) == 4
        assert len(invalid) == 1

    def test_filters_visits_with_null_service_date(self):
        df = make_visits()
        df.loc[0, "service_date"] = None
        valid, invalid = clean_service_visits(df)
        assert len(valid) == 4


class TestCleanClaims:
    def test_filters_claims_with_null_claim_id(self):
        claims = pd.DataFrame({
            "claim_id": ["CM000001", None, "CM000003"],
            "visit_id": ["VS0000001", "VS0000002", "VS0000003"],
            "client_id": ["CL00001", "CL00002", "CL00003"],
            "funder_id": ["FN001", "FN002", "FN003"],
            "claim_date": pd.to_datetime(["2024-01-01", "2024-01-02", "2024-01-03"]).date,
            "claim_amount": [100.0, 200.0, 300.0],
            "claim_status": ["Approved", "Rejected", "Approved"],
        })
        valid, invalid = clean_claims(claims)
        assert len(valid) == 2
        assert len(invalid) == 1

    def test_filters_claims_with_negative_amount(self):
        claims = pd.DataFrame({
            "claim_id": ["CM000001"],
            "visit_id": ["VS0000001"],
            "client_id": ["CL00001"],
            "funder_id": ["FN001"],
            "claim_date": pd.to_datetime(["2024-01-01"]).date,
            "claim_amount": [-50.0],
            "claim_status": ["Approved"],
        })
        valid, invalid = clean_claims(claims)
        assert len(valid) == 0
        assert len(invalid) == 1


class TestCleanFundingAllocations:
    def test_filters_allocations_with_null_allocation_id(self):
        df = pd.DataFrame({
            "allocation_id": [None, "AL00002"],
            "client_id": ["CL00001", "CL00002"],
            "funder_id": ["FN001", "FN002"],
            "allocation_start_date": pd.to_datetime(["2024-01-01", "2024-01-02"]).date,
            "allocation_end_date": pd.to_datetime(["2025-01-01", "2025-01-02"]).date,
            "allocated_amount": [10000.0, 20000.0],
            "approved_hours": [100.0, 200.0],
        })
        valid, invalid = clean_funding_allocations(df)
        assert len(valid) == 1
        assert len(invalid) == 1


class TestCleanReconciliationExceptions:
    def test_filters_exceptions_with_null_exception_id(self):
        df = pd.DataFrame({
            "exception_id": [None, "EX00002"],
            "claim_id": ["CM000001", "CM000002"],
            "exception_type": ["Amount Discrepancy", "Duplicate Claim"],
            "detected_date": pd.to_datetime(["2024-01-01", "2024-01-02"]).date,
            "exception_status": ["Open", "Resolved"],
            "exception_amount": [500.0, 1000.0],
            "priority": ["High", "Low"],
        })
        valid, invalid = clean_reconciliation_exceptions(df)
        assert len(valid) == 1
        assert len(invalid) == 1


class TestApplyAllCleaning:
    def test_applies_all_cleaners_and_returns_dicts(self):
        data = {
            "clients": make_clients(),
            "workers": make_workers(),
            "funders": pd.DataFrame({
                "funder_id": ["FN001"], "funder_name": ["Test"], "funding_type": ["Provincial"],
                "claim_limit": [100000.0], "documentation_sla_days": [14],
            }),
            "funding_allocations": pd.DataFrame({
                "allocation_id": ["AL00001"], "client_id": ["CL00001"], "funder_id": ["FN001"],
                "allocation_start_date": pd.to_datetime(["2024-01-01"]).date,
                "allocation_end_date": pd.to_datetime(["2025-01-01"]).date,
                "allocated_amount": [10000.0], "approved_hours": [100.0],
            }),
            "service_visits": make_visits(),
            "claims": pd.DataFrame({
                "claim_id": ["CM000001"], "visit_id": ["VS0000001"], "client_id": ["CL00001"],
                "funder_id": ["FN001"], "claim_date": pd.to_datetime(["2024-01-01"]).date,
                "claim_amount": [100.0], "claim_status": ["Approved"],
            }),
            "reconciliation_exceptions": pd.DataFrame({
                "exception_id": ["EX00001"], "claim_id": ["CM000001"], "exception_type": ["Amount Discrepancy"],
                "detected_date": pd.to_datetime(["2024-01-01"]).date,
                "exception_status": ["Open"], "exception_amount": [500.0], "priority": ["High"],
            }),
        }
        cleaned, rejected = apply_all_cleaning(data)
        assert "clients" in cleaned
        assert "service_visits" in cleaned
        assert isinstance(cleaned["clients"], pd.DataFrame)
        for name, df in cleaned.items():
            assert len(df) > 0, f"Cleaned {name} is empty"
