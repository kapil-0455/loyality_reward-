from backend.app.agents.router_agent import run_router_agent


def test_customer_recommendation_routing():
    result = run_router_agent("Suggest a reward for me", "customer")

    assert result["status"] == "SUCCESS"
    assert result["intent"] == "recommendation"
    assert result["route"] == "recommendation_agent"


def test_customer_redemption_routing():
    result = run_router_agent("I want to redeem my reward", "customer")

    assert result["status"] == "SUCCESS"
    assert result["route"] == "redemption_agent"


def test_admin_campaign_routing():
    result = run_router_agent("Show campaign budget", "admin")

    assert result["status"] == "SUCCESS"
    assert result["intent"] == "campaign"
    assert result["route"] == "campaign_agent"


def test_customer_cannot_access_admin_route():
    result = run_router_agent("Check inventory", "customer")

    assert result["status"] == "UNSUPPORTED_INTENT"
    assert result["route"] is None


def test_invalid_role_is_rejected():
    result = run_router_agent("Show campaign budget", "unknown")

    assert result["status"] == "UNAUTHORIZED"


def test_empty_request_is_rejected():
    result = run_router_agent("", "customer")

    assert result["status"] == "INVALID_REQUEST"
