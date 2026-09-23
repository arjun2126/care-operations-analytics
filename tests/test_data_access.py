import pytest
import pandas as pd
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.data_access import (
    _find_project_root,
    load_processed_data,
    get_data_source_status,
    load_claims_with_details,
    load_funding_with_claims,
    PROCESSED_DIR,
)


class TestProjectRoot:
    def test_project_root_contains_data_dir(self):
        root = _find_project_root()
        assert (root / "data" / "processed").is_dir() or (root / "data").is_dir()

    def test_processed_dir_exists(self):
        assert os.path.isdir(PROCESSED_DIR) or os.path.isdir(str(PROCESSED_DIR))


class TestDataSourceStatus:
    def test_returns_dict_with_all_loaded(self):
        status = get_data_source_status()
        assert "all_loaded" in status
        assert "tables" in status

    def test_tables_key(self):
        status = get_data_source_status()
        for name in ["clients", "workers", "funders", "funding_allocations", "service_visits", "claims", "reconciliation_exceptions"]:
            assert name in status["tables"]


class TestMissingDataError:
    def test_error_message_contains_command(self):
        from app.data_access import _require_processed_files
        try:
            _require_processed_files()
        except FileNotFoundError as e:
            assert "python -m src.pipeline" in str(e)


class TestLoadProcessedData:
    def test_loads_dataframes(self):
        data = load_processed_data()
        assert isinstance(data, dict)
        for name in ["clients", "workers", "funders", "funding_allocations", "service_visits", "claims", "reconciliation_exceptions"]:
            if name in data:
                assert isinstance(data[name], pd.DataFrame)

    def test_claims_has_required_columns(self):
        data = load_processed_data()
        if "claims" in data:
            assert "claim_id" in data["claims"].columns
            assert "claim_status" in data["claims"].columns