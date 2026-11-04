
from unittest.mock import Mock

from backend.app.agents.response_agent import run_response_agent


def get_test_data():
    return (
        {"customer_id": 101, "loyalty_tier": "Gold"},
        {"status": "SUCCESS", "recommendations": ["R101"]},
        {"status": "SUCCESS", "analytics": {"cluster": 2}}
    )


def test_successful_response():
    customer, recommendation, analytics = get_test_data()

    llm = Mock()
    llm.invoke.return_value.content = "Your recommended reward is R101."

    result = run_response_agent(
        customer, recommendation, analytics, llm
    )

    assert result["status"] == "SUCCESS"
    assert "R101" in result["response"]
    llm.invoke.assert_called_once()


def test_empty_llm_response():
    customer, recommendation, analytics = get_test_data()

    llm = Mock()
    llm.invoke.return_value.content = "   "

    result = run_response_agent(
        customer, recommendation, analytics, llm
    )

    assert result["status"] == "EMPTY_LLM_RESPONSE"
    assert result["response"] is None


def test_llm_failure():
    customer, recommendation, analytics = get_test_data()

    llm = Mock()
    llm.invoke.side_effect = RuntimeError("Groq unavailable")

    result = run_response_agent(
        customer, recommendation, analytics, llm
    )

    assert result["status"] == "LLM_ERROR"
    assert result["response"] is None


def test_invalid_customer_context():
    result = run_response_agent(
        None, {}, {}, Mock()
    )

    assert result["status"] == "INVALID_INPUT"


def test_invalid_recommendation_result():
    result = run_response_agent(
        {}, None, {}, Mock()
    )

    assert result["status"] == "INVALID_INPUT"


def test_invalid_analytics_result():
    result = run_response_agent(
        {}, {}, None, Mock()
    )

    assert result["status"] == "INVALID_INPUT"
