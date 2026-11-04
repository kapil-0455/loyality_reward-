from dataclasses import asdict, is_dataclass

from backend.app.agents.router_agent import run_router_agent
from backend.app.agents.data_agent import run_data_agent
from backend.app.agents.analytics_agent import run_analytics_agent
from backend.app.agents.eligibility_agent import run_eligibility_agent
from backend.app.agents.reward_agent import run_reward_agent
from backend.app.agents.response_agent import run_response_agent


def build_agent_nodes(mcp_client, llm=None, laya_router=None):

    # 1. Router Agent
    def router_node(state):
        result = run_router_agent(
            request=state.get("request"),
            user_role=state.get("user_role"),
        )

        return {
            "intent": result.get("intent"),
            "route": result.get("route"),
            "status": result.get("status"),
        }

    # 2. Data Agent
    async def data_node(state):

        customer_id = state.get("customer_id")

        # Fetch customer and transaction data
        requests = [
            ("customer", {"customer_id": customer_id}),
            ("transactions", {"customer_id": customer_id}),
            ("active_rewards", {}),
        ]

        data = {}

        for request_type, parameters in requests:
            result = await run_data_agent(
                mcp_client=mcp_client,
                request_type=request_type,
                parameters=parameters,
            )

            if result.get("status") != "SUCCESS":
                return {
                    "status": result.get("status"),
                    "error": result.get(
                        "error", f"{request_type} retrieval failed"
                    ),
                }

            data[request_type] = result.get("data")

        customer = data["customer"]
        transactions = data["transactions"]
        active_rewards = data["active_rewards"]

        if not isinstance(customer, dict):
            return {
                "status": "INVALID_CUSTOMER",
                "error": "Invalid customer data received from MCP",
            }

        if not isinstance(active_rewards, list):
            return {
                "status": "INVALID_REWARDS",
                "error": "Active rewards must be a list",
            }

        customer_context = {
            **customer,
            "customer_id": customer_id,
        }

        reward_contexts = []
        campaign_cache = {}

        # Fetch campaign, mappings and inventory for every reward
        for reward_record in active_rewards:

            if not isinstance(reward_record, dict):
                return {
                    "status": "INVALID_REWARD",
                    "error": "Invalid reward record received from MCP",
                }

            reward = dict(reward_record)

            reward_id = reward.get("reward_id")
            campaign_id = reward.get("campaign_id")

            if not reward_id or not campaign_id:
                return {
                    "status": "INVALID_REWARD",
                    "error": "Reward is missing reward_id or campaign_id",
                }

            # Fetch campaign details (reuse cached campaign data)
            if campaign_id not in campaign_cache:

                campaign_result = await run_data_agent(
                    mcp_client=mcp_client,
                    request_type="campaign",
                    parameters={"campaign_id": campaign_id},
                )

                if campaign_result.get("status") != "SUCCESS":
                    return {
                        "status": campaign_result.get("status"),
                        "error": campaign_result.get(
                            "error",
                            f"Campaign retrieval failed: {campaign_id}",
                        ),
                    }

                campaign_data = campaign_result.get("data")

                if not isinstance(campaign_data, dict):
                    return {
                        "status": "INVALID_CAMPAIGN",
                        "error": f"Invalid campaign data: {campaign_id}",
                    }

                campaign_data = dict(campaign_data)

                if "campaign_status" in campaign_data:
                    campaign_data["status"] = campaign_data.pop(
                        "campaign_status"
                    )

                campaign_cache[campaign_id] = campaign_data

            campaign = dict(campaign_cache[campaign_id])

            # Fetch reward-product mappings
            mapping_result = await run_data_agent(
                mcp_client=mcp_client,
                request_type="reward_mappings",
                parameters={"reward_id": reward_id},
            )

            if mapping_result.get("status") != "SUCCESS":
                return {
                    "status": mapping_result.get("status"),
                    "error": mapping_result.get(
                        "error",
                        f"Mapping retrieval failed: {reward_id}",
                    ),
                }

            mappings = mapping_result.get("data")

            if not isinstance(mappings, list):
                return {
                    "status": "INVALID_MAPPINGS",
                    "error": f"Invalid mappings for reward: {reward_id}",
                }

            inventories = []

            # Fetch inventory for every mapped product
            for mapping in mappings:

                if not isinstance(mapping, dict):
                    return {
                        "status": "INVALID_MAPPING",
                        "error": f"Invalid mapping for reward: {reward_id}",
                    }

                product_id = mapping.get("product_id")

                if not product_id:
                    return {
                        "status": "INVALID_MAPPING",
                        "error": f"Mapping is missing product_id: {reward_id}",
                    }

                if mapping.get("minimum_stock_required") is None:
                    return {
                        "status": "INVALID_MAPPING",
                        "error": (
                            f"Mapping is missing minimum_stock_required: "
                            f"{reward_id}"
                        ),
                    }

                inventory_result = await run_data_agent(
                    mcp_client=mcp_client,
                    request_type="inventory",
                    parameters={"product_id": product_id},
                )

                if inventory_result.get("status") != "SUCCESS":
                    return {
                        "status": inventory_result.get("status"),
                        "error": inventory_result.get(
                            "error",
                            f"Inventory retrieval failed: {product_id}",
                        ),
                    }

                inventory = inventory_result.get("data")

                if not isinstance(inventory, dict):
                    return {
                        "status": "INVALID_INVENTORY",
                        "error": f"Invalid inventory for product: {product_id}",
                    }

                inventory = dict(inventory)

                inventory["product_id"] = product_id
                inventory["required_quantity"] = mapping[
                    "minimum_stock_required"
                ]

                inventory["minimum_stock_level"] = inventory.pop(
                    "reorder_level", 0
                )

                inventory["replenishment_quantity"] = 0

                inventories.append(inventory)

            # Existing project convention
            reward["reward_cost"] = reward.get("reward_value")

            reward_contexts.append({
                "reward": reward,
                "campaign": campaign,
                "mappings": mappings,
                "inventory": inventories,
            })

        # Keep legacy single-reward fields for compatibility
        first_context = reward_contexts[0] if reward_contexts else {}

        return {
            "status": "SUCCESS",
            "customer_data": customer,
            "customer_context": customer_context,
            "transaction_data": transactions,

            # All rewards and their associated data
            "reward_data": reward_contexts,
            "inventory_data": [
                item["inventory"] for item in reward_contexts
            ],
            "campaign_data": [
                item["campaign"] for item in reward_contexts
            ],

            # Legacy fields
            "reward": first_context.get("reward"),
            "inventory": first_context.get("inventory", []),
            "campaign": first_context.get("campaign"),
            "reward_mappings": first_context.get("mappings", []),
        }

    # 3. Analytics Agent
    def analytics_node(state):

        customer_id = state.get("customer_id")

        result = run_analytics_agent(customer_id=customer_id)

        if result.get("status") != "SUCCESS":
            return {
                "status": result.get("status"),
                "error": result.get("error", "Analytics failed"),
                "analytics_result": result,
            }

        analytics = result.get("analytics", {})

        customer_context = {
            **(state.get("customer_context") or {}),
            **analytics,
        }

        return {
            "status": "SUCCESS",
            "analytics_result": result,
            "customer_context": customer_context,
        }

    # 4. Eligibility Agent
    def eligibility_node(state):

        customer = state.get("customer_data") or state.get("customer")
        reward_contexts = state.get("reward_data", [])

        eligibility_results = []
        feasible_candidates = []

        # Check every reward independently
        for item in reward_contexts:

            result = run_eligibility_agent(
                customer=customer,
                reward=item["reward"],
                inventory=item["inventory"],
                campaign=item["campaign"],
                evaluation_date=state.get("evaluation_date"),
                purchase_value=state.get("purchase_value", 0),
            )

            eligibility_results.append(result)

            if result.get("status") != "SUCCESS":
                return {
                    "eligibility_results": eligibility_results,
                    "feasible_candidates": [],
                    "status": result.get("status"),
                    "error": result.get(
                        "error", "Reward eligibility check failed"
                    ),
                }

            if result.get("eligible") is True:
                feasible_candidates.append(result["candidate"])

        return {
            "eligibility_results": eligibility_results,
            "feasible_candidates": feasible_candidates,
            "status": "SUCCESS",
            "error": None,
        }

    # 5. Reward Agent
    def reward_node(state):

        result = run_reward_agent(
            customer_context=state.get("customer_context", {}),
            feasible_candidates=state.get("feasible_candidates", []),
            router=laya_router,
        )

        recommendations = [
            asdict(item) if is_dataclass(item) else item
            for item in result
        ]

        recommendation_result = {
            "status": (
                "SUCCESS" if recommendations else "NO_FEASIBLE_REWARD"
            ),
            "recommendations": recommendations,
        }

        return {
            "recommendation_result": recommendation_result,
            "status": recommendation_result["status"],
        }

    # 6. Response Agent
    def response_node(state):

        result = run_response_agent(
            customer_context=state.get("customer_context", {}),
            recommendation_result=state.get("recommendation_result", {}),
            analytics_result=state.get("analytics_result", {}),
            llm=llm,
        )

        return {
            "final_response": result.get("response"),
            "status": result.get("status"),
            "error": result.get("error"),
        }

    return {
        "router": router_node,
        "data": data_node,
        "analytics": analytics_node,
        "eligibility": eligibility_node,
        "reward": reward_node,
        "response": response_node,
    }