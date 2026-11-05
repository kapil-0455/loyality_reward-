import os
import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.api.security import require_campaign_manager
from backend.app.api.routes import approvals, redemptions


@pytest.fixture
def client():
    app.dependency_overrides.clear()
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_approval_500_does_not_leak_database_credentials(client, monkeypatch):
    """When an unexpected internal error occurs during approval, no DB credentials or tracebacks leak in response."""
    app.dependency_overrides[require_campaign_manager] = lambda: True

    def fail_with_db_error(db, request):
        raise RuntimeError(
            "postgresql://admin:super_secret_password_123@db-host:5432/production_db connection refused"
        )

    monkeypatch.setattr(approvals, "approve_reward", fail_with_db_error)

    payload = {
        "customer_id": 12347,
        "reward_id": "REWARD-001",
        "campaign_id": "CAMP-001",
        "purchase_value": 1000,
        "evaluation_date": "2026-11-05",
        "approved": True,
        "idempotency_key": "leak-test-app-001",
    }

    response = client.post("/rewards/approvals", json=payload)

    assert response.status_code == 500
    content = response.text
    # Sensitive items must NOT leak
    assert "super_secret_password_123" not in content
    assert "postgresql://" not in content
    assert "production_db" not in content
    assert response.json()["detail"] == "Internal server error while processing approval"


def test_redemption_500_does_not_leak_database_credentials(client, monkeypatch):
    """When an unexpected internal error occurs during redemption, no DB credentials or tracebacks leak in response."""
    app.dependency_overrides[require_campaign_manager] = lambda: True

    def fail_with_db_error(db, request):
        raise RuntimeError(
            "postgresql://neondb_owner:secret_neon_key_999@ep-pooler.aws.neon.tech/neondb failed"
        )

    monkeypatch.setattr(redemptions, "redeem_reward", fail_with_db_error)

    payload = {
        "approval_id": "app-001",
        "customer_id": 12347,
        "reward_id": "REWARD-001",
        "campaign_id": "CAMP-001",
        "idempotency_key": "leak-test-red-001",
    }

    response = client.post("/rewards/redemptions", json=payload)

    assert response.status_code == 500
    content = response.text
    assert "secret_neon_key_999" not in content
    assert "neon.tech" not in content
    assert response.json()["detail"] == "Internal server error while redeeming reward"


def test_health_check_does_not_expose_environment_variables(client):
    """Health check endpoint must only return safe status, never environment secrets."""
    response = client.get("/health")
    assert response.status_code == 200

    data = response.json()
    assert data == {"status": "healthy"}

    # Verify no env secrets in raw text
    for secret_env in ["DATABASE_URL", "OPENAI_API_KEY", "CAMPAIGN_MANAGER_API_TOKEN", "GROQ_API_KEY"]:
        secret_val = os.getenv(secret_env)
        if secret_val and len(secret_val) > 4:
            assert secret_val not in response.text


def test_auth_failure_does_not_reveal_token_value(client, monkeypatch):
    """401 responses for invalid tokens must never disclose the valid token value."""
    secret_token = "manager-secret-token-xyz-123456"
    monkeypatch.setenv("CAMPAIGN_MANAGER_API_TOKEN", secret_token)

    response = client.post(
        "/rewards/approvals",
        json={},
        headers={"Authorization": "Bearer attacker-guessed-token"},
    )

    assert response.status_code == 401
    assert secret_token not in response.text
    assert response.json()["detail"] == "Campaign manager authentication required"
