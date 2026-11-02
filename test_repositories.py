
from backend.app.db.repositories.campaign_repository import (
    get_active_campaigns,
    get_all_campaigns,
    get_available_budget,
)
from backend.app.db.repositories.customer_repository import (
    get_customer_by_id,
    get_customer_count,
)
from backend.app.db.repositories.inventory_repository import (
    get_all_inventory,
    get_product_inventory,
)
from backend.app.db.repositories.redemption_repository import (
    get_customer_redemptions,
)
from backend.app.db.repositories.reward_repository import (
    get_active_rewards,
    get_all_rewards,
)
from backend.app.db.session import SessionLocal

db = SessionLocal()

try:
    print("Customers:", get_customer_count(db))

    customer = get_customer_by_id(db, 12346)
    print("Customer found:", customer is not None)

    print("Rewards:", len(get_all_rewards(db)))
    print("Active rewards:", len(get_active_rewards(db)))

    print("Inventory:", len(get_all_inventory(db)))

    inventory = get_product_inventory(db, "SYN-PROD-001")
    print("Inventory lookup:", inventory is not None)

    print("Campaigns:", len(get_all_campaigns(db)))
    print("Active campaigns:", len(get_active_campaigns(db)))

    print(
        "Available budget:",
        get_available_budget(db, "SYN-CAMP-001")
    )

    print(
        "Customer redemptions:",
        len(get_customer_redemptions(db, 12346))
    )

    print("Repository tests completed!")

except Exception as e:
    print("Repository test failed:", e)

finally:
    db.close()
