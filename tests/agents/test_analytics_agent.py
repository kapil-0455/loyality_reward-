
import pandas as pd

from backend.app.agents import analytics_agent


def create_test_datasets(tmp_path):
    rfm_file = tmp_path / "rfm.csv"
    segment_file = tmp_path / "segments.csv"
    loyalty_file = tmp_path / "loyalty.csv"

    pd.DataFrame([
        {
            "customer_id": "101",
            "recency": 10,
            "frequency": 5,
            "monetary": 2500,
            "last_purchase_date": "2026-10-01"
        }
    ]).to_csv(rfm_file, index=False)

    pd.DataFrame([
        {"customer_id": "101", "cluster": 2}
    ]).to_csv(segment_file, index=False)

    pd.DataFrame([
        {
            "customer_id": "101",
            "loyalty_tier": "Gold",
            "points_balance": 500
        }
    ]).to_csv(loyalty_file, index=False)

    analytics_agent.RFM_FILE = rfm_file
    analytics_agent.SEGMENT_FILE = segment_file
    analytics_agent.LOYALTY_FILE = loyalty_file


def test_successful_analytics(tmp_path):
    create_test_datasets(tmp_path)

    result = analytics_agent.run_analytics_agent(101)

    assert result["status"] == "SUCCESS"
    assert result["analytics"]["recency"] == 10
    assert result["analytics"]["cluster"] == 2
    assert result["analytics"]["loyalty_tier"] == "Gold"


def test_invalid_customer_id():
    result = analytics_agent.run_analytics_agent(None)

    assert result["status"] == "INVALID_CUSTOMER_ID"


def test_customer_not_found(tmp_path):
    create_test_datasets(tmp_path)

    result = analytics_agent.run_analytics_agent(999)

    assert result["status"] == "CUSTOMER_DATA_NOT_FOUND"


def test_duplicate_customer_data(tmp_path):
    create_test_datasets(tmp_path)

    pd.DataFrame([
        {"customer_id": "101", "cluster": 2},
        {"customer_id": "101", "cluster": 3}
    ]).to_csv(analytics_agent.SEGMENT_FILE, index=False)

    result = analytics_agent.run_analytics_agent(101)

    assert result["status"] == "DUPLICATE_CUSTOMER_DATA"


def test_missing_dataset(tmp_path):
    create_test_datasets(tmp_path)

    analytics_agent.RFM_FILE = tmp_path / "missing.csv"

    result = analytics_agent.run_analytics_agent(101)

    assert result["status"] == "DATASET_NOT_FOUND"
