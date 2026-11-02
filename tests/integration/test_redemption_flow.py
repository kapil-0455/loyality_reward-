
from datetime import date
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.main import app
from backend.app.api.routes import approvals, redemptions
from backend.app.db.models import (
    Base,
    CustomerLoyaltyProfile,
    CampaignBudget,
    InventorySnapshot,
    RewardCatalogue,
    RewardProductMapping,
    RewardApproval,
    RewardLedger,
)


@pytest.fixture
def db():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    Base.metadata.create_all(bind=engine)

    TestingSession = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
    )

    session = TestingSession()

    customer = CustomerLoyaltyProfile(
        customer_id=12347,
        loyalty_tier="Gold",
        points_balance=5000,
        profile_status="active",
        is_synthetic=True,
    )

    campaign = CampaignBudget(
        campaign_id="CAMP-001",
        budget_limit=Decimal("50000"),
        committed_amount=Decimal("5000"),
        approved_amount=Decimal("0"),
        campaign_status="active",
        is_synthetic=True,
        available_budget_before_approval=Decimal("45000"),
    )

    reward = RewardCatalogue(
        reward_id="REWARD-001",
        reward_name="Test Reward",
        reward_type="product",
        reward_value=Decimal("1730"),
        points_required=1718,
        eligible_tiers="Silver,Gold",
        valid_from=date(2011, 11, 1),
        valid_until=date(2012, 3, 31),
        minimum_purchase_value=Decimal("500"),
        status="active",
        campaign_id="CAMP-001",
        is_synthetic=True,
    )

    inventory = InventorySnapshot(
        product_id="PROD-001",
        on_hand_stock=100,
        reserved_stock=0,
        reorder_level=10,
        replenishment_date=date(2012, 1, 1),
        is_synthetic=True,
        available_stock=100,
    )

    mapping = RewardProductMapping(
        reward_id="REWARD-001",
        product_id="PROD-001",
        minimum_stock_required=2,
        inventory_constraint_type="HARD",
        is_synthetic=True,
    )

    session.add_all([
        customer,
        campaign,
        reward,
        inventory,
        mapping,
    ])

    session.commit()

    yield session

    session.close()
    engine.dispose()


@pytest.fixture
def client(db):
    def override_get_db():
        yield db

    app.dependency_overrides[approvals.get_db] = override_get_db
    app.dependency_overrides[redemptions.get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


def test_complete_approval_redemption_flow(client, db):

    # 1. Approval API
    approval_response = client.post(
        "/rewards/approvals",
        json={
            "customer_id": 12347,
            "reward_id": "REWARD-001",
            "campaign_id": "CAMP-001",
            "purchase_value": 1000,
            "evaluation_date": "2011-12-10",
            "approved": True,
            "idempotency_key": "integration-approval-001",
        },
    )

    print("Approval Status:", approval_response.status_code)
    print("Approval Response:", approval_response.text)

    assert approval_response.status_code == 200

    approval_id = approval_response.json()["approval_id"]

    # 2. Redemption API
    redemption_response = client.post(
        "/rewards/redemptions",
        json={
            "approval_id": approval_id,
            "customer_id": 12347,
            "reward_id": "REWARD-001",
            "campaign_id": "CAMP-001",
            "idempotency_key": "integration-redemption-001",
        },
    )

    print("Redemption Status:", redemption_response.status_code)
    print("Redemption Response:", redemption_response.text)

    assert redemption_response.status_code == 200
    assert redemption_response.json()["status"] == "REDEEMED"

    # 3. Customer points verification
    customer = db.query(CustomerLoyaltyProfile).first()

    assert customer.points_balance == 3282

    # 4. Campaign budget verification
    campaign = db.query(CampaignBudget).first()

    assert campaign.approved_amount == Decimal("0")
    assert campaign.committed_amount == Decimal("6730")

    # 5. Inventory verification
    inventory = db.query(InventorySnapshot).first()

    assert inventory.on_hand_stock == 98
    assert inventory.reserved_stock == 0
    assert inventory.available_stock == 98

    # 6. Approval status verification
    approval = db.query(RewardApproval).first()

    assert approval.approval_status == "REDEEMED"

    # 7. Ledger verification
    ledger = db.query(RewardLedger).all()

    assert len(ledger) == 1
    assert ledger[0].redemption_status == "REDEEMED"
    assert ledger[0].points_debited == 1718
