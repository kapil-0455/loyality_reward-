from backend.app.agents.graph_nodes import build_agent_nodes


class MockLayaRouter:
    def predict(self, state, questions, model=None):
        reward_id = state["rewards"][0]

        return {
            "answers": {
                "reward_choice": {"choice": reward_id, "answer_confidence": 0.90}
            }
        }


def get_test_state():

    return {
        "customer": {
            "profile_status": "active",
            "loyalty_tier": "Gold",
            "points_balance": 1000,
        },
        "reward": {
            "reward_id": "R101",
            "reward_name": "Discount Reward",
            "reward_type": "discount",
            "reward_value": 100,
            "reward_cost": 100,
            "points_required": 200,
            "campaign_id": "C101",
            "status": "active",
            "valid_from": "2026-01-01",
            "valid_until": "2026-12-31",
            "eligible_tiers": "Gold,Silver",
            "minimum_purchase_value": None,
        },
        "inventory": {
            "on_hand_stock": 20,
            "reserved_stock": 2,
            "required_quantity": 1,
            "minimum_stock_level": 5,
            "replenishment_quantity": 0,
        },
        "campaign": {
            "budget_limit": 10000,
            "committed_amount": 1000,
            "approved_amount": 500,
            "status": "active",
        },
        "evaluation_date": "2026-11-04",
        "purchase_value": 0,
        "customer_context": {
            "customer_id": 101,
            "loyalty_tier": "Gold",
            "points_balance": 1000,
        },
    }


def test_eligibility_and_reward_selection():

    nodes = build_agent_nodes(mcp_client=None, laya_router=MockLayaRouter())

    state = get_test_state()

    # Run actual Eligibility Agent node
    eligibility_result = nodes["eligibility"](state)

    assert eligibility_result["status"] == "SUCCESS"
    assert len(eligibility_result["feasible_candidates"]) == 1

    # Pass only feasible candidates to Reward Agent
    state.update(eligibility_result)

    reward_result = nodes["reward"](state)

    assert reward_result["status"] == "SUCCESS"

    selected = reward_result["recommendation_result"]["recommendations"]

    assert len(selected) == 1
    assert selected[0]["candidate"]["reward_id"] == "R101"


def test_ineligible_reward_never_reaches_laya():

    nodes = build_agent_nodes(mcp_client=None, laya_router=MockLayaRouter())

    state = get_test_state()

    # Insufficient customer points
    state["customer"]["points_balance"] = 50

    eligibility_result = nodes["eligibility"](state)

    assert eligibility_result["status"] == "SUCCESS"
    assert eligibility_result["feasible_candidates"] == []

    state.update(eligibility_result)

    reward_result = nodes["reward"](state)

    assert reward_result["status"] == "NO_FEASIBLE_REWARD"
    assert reward_result["recommendation_result"]["recommendations"] == []
