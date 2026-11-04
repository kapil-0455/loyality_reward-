
def run_router_agent(request, user_role):
    """
    Identifies request intent and routes it
    to the appropriate agent workflow.

    user_role must come from authenticated user data,
    not from the user's message.
    """

    if not isinstance(request, str) or not request.strip():
        return {
            "status": "INVALID_REQUEST",
            "intent": None,
            "route": None
        }

    if user_role not in ["customer", "admin"]:
        return {
            "status": "UNAUTHORIZED",
            "intent": None,
            "route": None
        }

    message = request.lower()

    # Customer intents
    customer_intents = {
        "recommendation": [
            "recommend", "suggest reward", "best reward",
            "reward for me"
        ],
        "approval": [
            "approve", "request reward", "claim reward"
        ],
        "redemption": [
            "redeem", "use my points", "claim my reward"
        ],
        "profile": [
            "my profile", "my points", "points balance",
            "my loyalty"
        ],
        "segment": [
            "my segment", "customer segment"
        ]
    }

    # Admin intents
    admin_intents = {
        "inventory": [
            "inventory", "stock", "available products"
        ],
        "campaign": [
            "campaign", "campaign budget", "campaign performance"
        ],
        "analytics": [
            "analytics", "customer analysis",
            "customer segmentation", "sales report"
        ]
    }

    allowed_intents = (
        customer_intents
        if user_role == "customer"
        else admin_intents
    )

    for intent, keywords in allowed_intents.items():

        for keyword in keywords:

            if keyword in message:
                return {
                    "status": "SUCCESS",
                    "intent": intent,
                    "route": f"{intent}_agent"
                }

    return {
        "status": "UNSUPPORTED_INTENT",
        "intent": None,
        "route": None
    }
