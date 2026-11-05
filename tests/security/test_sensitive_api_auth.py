import pytest
from fastapi.testclient import TestClient

from backend.app.main import app


PROTECTED_REQUESTS = [
    (
        "post",
        "/rewards/approvals",
        {
            "customer_id": 12347,
            "reward_id": "REWARD-001",
            "campaign_id": "CAMP-001",
            "purchase_value": 1000,
            "evaluation_date": "2026-11-05",
            "approved": True,
            "idempotency_key": "security-approval-001",
        },
    ),
    (
        "post",
        "/rewards/redemptions",
        {
            "approval_id": "approval-001",
            "customer_id": 12347,
            "reward_id": "REWARD-001",
            "campaign_id": "CAMP-001",
            "idempotency_key": "security-redemption-001",
        },
    ),
    ("get", "/rewards/redemptions/redemption-001", None),
]


@pytest.fixture
def client():
    app.dependency_overrides.clear()
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def send_request(client, method, path, payload, token=None):
    headers = {}
    if token is not None:
        headers["Authorization"] = f"Bearer {token}"

    if method == "post":
        return client.post(path, json=payload, headers=headers)

    return client.get(path, headers=headers)


@pytest.mark.parametrize("method,path,payload", PROTECTED_REQUESTS)
def test_sensitive_routes_reject_missing_token(
    client, monkeypatch, method, path, payload
):
    monkeypatch.setenv("CAMPAIGN_MANAGER_API_TOKEN", "test-manager-secret")

    response = send_request(client, method, path, payload)

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


@pytest.mark.parametrize("method,path,payload", PROTECTED_REQUESTS)
def test_sensitive_routes_reject_invalid_token(
    client, monkeypatch, method, path, payload
):
    monkeypatch.setenv("CAMPAIGN_MANAGER_API_TOKEN", "test-manager-secret")

    response = send_request(
        client, method, path, payload, token="wrong-token"
    )

    assert response.status_code == 401


@pytest.mark.parametrize("method,path,payload", PROTECTED_REQUESTS)
def test_sensitive_routes_fail_closed_when_token_not_configured(
    client, monkeypatch, method, path, payload
):
    monkeypatch.delenv("CAMPAIGN_MANAGER_API_TOKEN", raising=False)

    response = send_request(
        client, method, path, payload, token="any-token"
    )

    assert response.status_code == 503
    assert response.json()["detail"] == (
        "Campaign manager authentication is not configured"
    )
