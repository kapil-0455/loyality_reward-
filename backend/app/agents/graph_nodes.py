
"""
LangGraph Agent Nodes
Connects all six agents with the shared graph state.
"""

from dataclasses import asdict, is_dataclass

from backend.app.agents.analytics_agent import run_analytics_agent
from backend.app.agents.data_agent import run_data_agent
from backend.app.agents.eligibility_agent import run_eligibility_agent
from backend.app.agents.response_agent import run_response_agent
from backend.app.agents.reward_agent import run_reward_agent
from backend.app.agents.router_agent import run_router_agent


def build_agent_nodes(mcp_client, llm=None, laya_router=None):

    # 1. Router Agent
    def router_node(state):
        result = run_router_agent(
            request=state.get("request"),
            user_role=state.get("user_role")
        )

        return {
            "intent": result.get("intent"),
            "route": result.get("route"),
            "status": result.get("status")
        }

    # 2. Data Agent
    async def data_node(state):
        result = await run_data_agent(
            mcp_client=mcp_client,
            request_type=state.get("data_request_type"),
            parameters=state.get("data_parameters", {})
        )

        request_type = state.get("data_request_type")

        output_keys = {
            "customer": "customer_data",
            "transactions": "transaction_data",
            "inventory": "inventory_data",
            "campaign": "campaign_data"
        }

        update = {
            "status": result.get("status"),
            "error": result.get("error")
        }

        if result.get("status") == "SUCCESS":
            output_key = output_keys[request_type]
            update[output_key] = result.get("data")

        return update

    # 3. Analytics Agent
    def analytics_node(state):
        result = run_analytics_agent(
            customer_id=state.get("customer_id")
        )

        return {
            "analytics_result": result,
            "status": result.get("status"),
            "error": result.get("error")
        }

    # 4. Eligibility Agent
    def eligibility_node(state):
        result = run_eligibility_agent(
            customer=state.get("customer"),
            reward=state.get("reward"),
            inventory=state.get("inventory"),
            campaign=state.get("campaign"),
            evaluation_date=state.get("evaluation_date"),
            purchase_value=state.get("purchase_value", 0)
        )

        feasible_candidates = []

        if (
            result.get("status") == "SUCCESS"
            and result.get("eligible") is True
        ):
            feasible_candidates.append(result["candidate"])

        return {
            "eligibility_results": [result],
            "feasible_candidates": feasible_candidates,
            "status": result.get("status"),
            "error": result.get("error")
        }

    # 5. Reward Agent
    def reward_node(state):
        result = run_reward_agent(
            customer_context=state.get("customer_context", {}),
            feasible_candidates=state.get("feasible_candidates", []),
            router=laya_router
        )

        recommendations = [
            asdict(item) if is_dataclass(item) else item
            for item in result
        ]

        return {
            "recommendation_result": {
                "status": "SUCCESS" if recommendations else "NO_FEASIBLE_REWARD",
                "recommendations": recommendations
            },
            "status": "SUCCESS" if recommendations else "NO_FEASIBLE_REWARD"
        }

    # 6. Response Agent
    def response_node(state):
        result = run_response_agent(
            customer_context=state.get("customer_context", {}),
            recommendation_result=state.get("recommendation_result", {}),
            analytics_result=state.get("analytics_result", {}),
            llm=llm
        )

        return {
            "final_response": result.get("response"),
            "status": result.get("status"),
            "error": result.get("error")
        }

    return {
        "router": router_node,
        "data": data_node,
        "analytics": analytics_node,
        "eligibility": eligibility_node,
        "reward": reward_node,
        "response": response_node
    }
