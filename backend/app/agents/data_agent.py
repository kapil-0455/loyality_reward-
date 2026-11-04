"""
Data Agent
Retrieves customer, transaction, inventory and campaign
data through approved MCP tools.
"""

ALLOWED_TOOLS = {
    "customer": {"tool": "get_customer_profile", "required": ["customer_id"]},
    "transactions": {"tool": "get_transaction_history", "required": ["customer_id"]},
    "inventory": {"tool": "get_product_inventory", "required": ["product_id"]},
    "campaign": {"tool": "get_campaign_details", "required": ["campaign_id"]},
    "reward": {"tool": "get_reward_details", "required": ["reward_id"]},
}


async def run_data_agent(mcp_client, request_type, parameters):

    if request_type not in ALLOWED_TOOLS:
        return {"status": "INVALID_REQUEST", "data": None}

    if not isinstance(parameters, dict):
        return {"status": "INVALID_PARAMETERS", "data": None}

    tool_config = ALLOWED_TOOLS[request_type]

    for key in tool_config["required"]:
        if key not in parameters or parameters[key] is None:
            return {
                "status": "MISSING_PARAMETER",
                "missing_parameter": key,
                "data": None,
            }

    if set(parameters.keys()) != set(tool_config["required"]):
        return {"status": "INVALID_PARAMETERS", "data": None}

    try:
        result = await mcp_client.call_tool(tool_config["tool"], parameters)

        # Check MCP tool execution error
        if getattr(result, "is_error", False):
            return {
                "status": "MCP_TOOL_ERROR",
                "request_type": request_type,
                "error": str(getattr(result, "content", result)),
                "data": None,
            }

        # Extract actual data from FastMCP CallToolResult
        payload = getattr(result, "data", result)

        if not isinstance(payload, dict):
            return {
                "status": "INVALID_TOOL_RESPONSE",
                "request_type": request_type,
                "data": None,
            }

        # Handle server-side response status
        tool_status = payload.get("status", "SUCCESS")

        if tool_status != "SUCCESS":
            return {
                "status": tool_status,
                "request_type": request_type,
                "error": payload.get("error"),
                "data": payload.get("data"),
            }

        # Return only usable data
        return {
            "status": "SUCCESS",
            "request_type": request_type,
            "data": payload.get("data", payload),
        }

    except Exception as error:
        return {
            "status": "MCP_TOOL_ERROR",
            "request_type": request_type,
            "error": str(error),
            "data": None,
        }
