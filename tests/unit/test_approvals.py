
import pytest
from types import SimpleNamespace
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.api.routes import approvals


@pytest.fixture
def client():
    def override_get_db():
        yield None

    app.dependency_overrides[approvals.get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def approval_payload():
    return {
        "customer_id": 12347,
        "reward_id": "SYN-REWARD-001",
        "campaign_id": "SYN-CAMP-001",
        "purchase_value": 1000,
        "evaluation_date": "2011-12-10",
        "approved": True,
        "idempotency_key": "test-approval-001",
    }


def test_successful_approval(client, approval_payload, monkeypatch):

    def fake_approve_reward(db, request):
        return SimpleNamespace(
            approval_id="test-approval-id",
            customer_id=12347,
            reward_id="SYN-REWARD-001",
            campaign_id="SYN-CAMP-001",
            approval_status="APPROVED",
        )

    monkeypatch.setattr(
        approvals,
        "approve_reward",
        fake_approve_reward
    )

    response = client.post(
        "/rewards/approvals",
        json=approval_payload
    )

    assert response.status_code == 200
    assert response.json()["approval_status"] == "APPROVED"


def test_invalid_approval(client, approval_payload, monkeypatch):

    def fake_approve_reward(db, request):
        raise ValueError("Customer not found")

    monkeypatch.setattr(
        approvals,
        "approve_reward",
        fake_approve_reward
    )

    response = client.post(
        "/rewards/approvals",
        json=approval_payload
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Customer not found"


def test_approval_server_error(client, approval_payload, monkeypatch):

    def fake_approve_reward(db, request):
        raise Exception("Database error")

    monkeypatch.setattr(
        approvals,
        "approve_reward",
        fake_approve_reward
    )

    response = client.post(
        "/rewards/approvals",
        json=approval_payload
    )

    assert response.status_code == 500
    assert response.json()["detail"] == (
        "Internal server error while processing approval"
    )
