import json
import logging
from fastapi.testclient import TestClient
import pytest

from backend.app.main import app
from backend.app.observability.logging import (
    StructuredJsonFormatter,
    mask_sensitive_dict,
)


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


def test_request_id_header_generated_when_missing(client):
    """Responses include an automatically generated X-Request-ID header."""
    response = client.get("/health")
    assert response.status_code == 200
    assert "x-request-id" in response.headers
    assert len(response.headers["x-request-id"]) > 0


def test_request_id_header_propagated_when_provided(client):
    """Client-provided X-Request-ID is preserved in response headers."""
    custom_id = "custom-client-trace-12345"
    response = client.get("/health", headers={"X-Request-ID": custom_id})
    assert response.status_code == 200
    assert response.headers.get("x-request-id") == custom_id


def test_structured_json_formatter_outputs_required_fields():
    """StructuredJsonFormatter outputs parseable JSON with request_id and outcome."""
    formatter = StructuredJsonFormatter()
    record = logging.LogRecord(
        name="test_logger",
        level=logging.INFO,
        pathname="test.py",
        lineno=10,
        msg="Transaction completed",
        args=(),
        exc_info=None,
    )
    record.request_id = "req-abc-123"
    record.status_code = 200
    record.latency_ms = 14.5
    record.outcome = "SUCCESS"

    formatted = formatter.format(record)
    parsed = json.loads(formatted)

    assert parsed["message"] == "Transaction completed"
    assert parsed["request_id"] == "req-abc-123"
    assert parsed["status_code"] == 200
    assert parsed["latency_ms"] == 14.5
    assert parsed["outcome"] == "SUCCESS"
    assert parsed["level"] == "INFO"
    assert "timestamp" in parsed


def test_sensitive_dict_masking():
    """mask_sensitive_dict masks authorization, tokens, passwords, and API keys."""
    raw = {
        "customer_id": 12347,
        "authorization": "Bearer secret_manager_token_123",
        "api_key": "sk-proj-xyz",
        "database_password": "super_secret_db_pass",
        "nested": {
            "token": "refresh_token_abc",
            "safe_field": "visible_value",
        },
    }

    masked = mask_sensitive_dict(raw)

    assert masked["customer_id"] == 12347
    assert masked["authorization"] == "***MASKED***"
    assert masked["api_key"] == "***MASKED***"
    assert masked["database_password"] == "***MASKED***"
    assert masked["nested"]["token"] == "***MASKED***"
    assert masked["nested"]["safe_field"] == "visible_value"

