
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.api.security import require_campaign_manager
from backend.app.api.routes import redemptions


@pytest.fixture
def client():
    def override_get_db():
        yield None

    app.dependency_overrides[require_campaign_manager] = lambda: True
    app.dependency_overrides[redemptions.get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def redemption_payload():
    return {
        "approval_id": "test-approval-001",
        "customer_id": 12347,
        "reward_id": "SYN-REWARD-001",
        "campaign_id": "SYN-CAMP-001",
        "idempotency_key": "test-redemption-001",
    }


def test_successful_redemption(client, redemption_payload, monkeypatch):

    def fake_redeem_reward(db, request):
        return SimpleNamespace(
            redemption_id="test-redemption-id",
            customer_id=12347,
            reward_id="SYN-REWARD-001",
            redemption_status="REDEEMED",
            points_debited=1718,
        )

    monkeypatch.setattr(
        redemptions,
        "redeem_reward",
        fake_redeem_reward
    )

    response = client.post(
        "/rewards/redemptions",
        json=redemption_payload
    )

    assert response.status_code == 200
    assert response.json()["status"] == "REDEEMED"
    assert response.json()["points_debited"] == 1718


def test_invalid_redemption(client, redemption_payload, monkeypatch):

    def fake_redeem_reward(db, request):
        raise ValueError("Approval not found")

    monkeypatch.setattr(
        redemptions,
        "redeem_reward",
        fake_redeem_reward
    )

    response = client.post(
        "/rewards/redemptions",
        json=redemption_payload
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Approval not found"


def test_internal_server_error(client, redemption_payload, monkeypatch):

    def fake_redeem_reward(db, request):
        raise Exception("Database error")

    monkeypatch.setattr(
        redemptions,
        "redeem_reward",
        fake_redeem_reward
    )

    response = client.post(
        "/rewards/redemptions",
        json=redemption_payload
    )

    assert response.status_code == 500
    assert response.json()["detail"] == (
        "Internal server error while redeeming reward"
    )
