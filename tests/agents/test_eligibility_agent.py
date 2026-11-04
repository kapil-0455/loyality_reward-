
from backend.app.agents.eligibility_agent import run_eligibility_agent


def get_test_data():
    customer = {
        "profile_status": "active",
        "loyalty_tier": "Gold",
        "points_balance": 1000
    }

    reward = {
        "reward_id": "R101",
        "reward_name": "Discount Reward",
        "reward_type": "discount",
        "reward_value": 100,
        "points_required": 200,
        "campaign_id": "C101",
        "status": "active",
        "valid_from": "2026-01-01",
        "valid_until": "2026-12-31",
        "eligible_tiers": "Gold,Silver",
        "minimum_purchase_value": None,
        "reward_cost": 50
    }

    inventory = {
        "on_hand_stock": 20,
        "reserved_stock": 2,
        "required_quantity": 1,
        "minimum_stock_level": 0,
        "replenishment_quantity": 0
    }

    campaign = {
        "budget_limit": 10000,
        "committed_amount": 1000,
        "approved_amount": 500,
        "status": "active"
    }

    return customer, reward, inventory, campaign


def test_successful_eligibility():
    customer, reward, inventory, campaign = get_test_data()

    result = run_eligibility_agent(
        customer, reward, inventory, campaign, "2026-11-04"
    )

    assert result["status"] == "SUCCESS"
    assert result["eligible"] is True
    assert result["reason_codes"] == []


def test_insufficient_customer_points():
    customer, reward, inventory, campaign = get_test_data()
    customer["points_balance"] = 100

    result = run_eligibility_agent(
        customer, reward, inventory, campaign, "2026-11-04"
    )

    assert result["status"] == "SUCCESS"
    assert result["eligible"] is False
    assert "INSUFFICIENT_POINTS" in result["reason_codes"]


def test_insufficient_inventory():
    customer, reward, inventory, campaign = get_test_data()
    inventory["on_hand_stock"] = 2
    inventory["reserved_stock"] = 1
    inventory["required_quantity"] = 5

    result = run_eligibility_agent(
        customer, reward, inventory, campaign, "2026-11-04"
    )

    assert result["status"] == "SUCCESS"
    assert result["eligible"] is False
    assert "INSUFFICIENT_STOCK" in result["reason_codes"]


def test_campaign_budget_exceeded():
    customer, reward, inventory, campaign = get_test_data()
    campaign["budget_limit"] = 1000
    campaign["committed_amount"] = 800
    campaign["approved_amount"] = 200
    reward["reward_cost"] = 100

    result = run_eligibility_agent(
        customer, reward, inventory, campaign, "2026-11-04"
    )

    assert result["status"] == "SUCCESS"
    assert result["eligible"] is False
    assert "BUDGET_EXCEEDED" in result["reason_codes"]


def test_invalid_input():
    result = run_eligibility_agent(
        None, {}, {}, {}, "2026-11-04"
    )

    assert result["status"] == "INVALID_INPUT"
    assert result["candidate"] is None
