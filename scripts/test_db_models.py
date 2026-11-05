
from backend.app.db.session import SessionLocal
from backend.app.db.models import CustomerLoyaltyProfile
from backend.app.db.models import (
    CampaignBudget,
    InventorySnapshot,
    RewardCatalogue,
    RewardProductMapping,
    RewardLedger
)

db = SessionLocal()

try:
    # Total customer profiles
    total_customers = db.query(CustomerLoyaltyProfile).count()
    print("Total customers:", total_customers)

    # Fetch first 5 customers
    customers = (
        db.query(CustomerLoyaltyProfile)
        .limit(5)
        .all()
    )

    for customer in customers:
        print(
            customer.customer_id,
            customer.loyalty_tier,
            customer.points_balance,
            customer.profile_status
        )

    print("SQLAlchemy model test successful!")
    print("\nCampaigns:", db.query(CampaignBudget).count())
    print("Inventory records:", db.query(InventorySnapshot).count())
    print("Rewards:", db.query(RewardCatalogue).count())
    print("Reward mappings:", db.query(RewardProductMapping).count())
    print("Ledger records:", db.query(RewardLedger).count())

except Exception as e:
    print("Database model test failed:", e)

finally:
    db.close()
