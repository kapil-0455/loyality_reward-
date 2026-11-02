
from datetime import date, datetime
from decimal import Decimal
from types import SimpleNamespace

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

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
from backend.app.services.redemption_service import redeem_reward


@pytest.fixture
def db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    TestingSession = sessionmaker(bind=engine)
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
        approved_amount=Decimal("1730"),
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
        reserved_stock=2,
        reorder_level=10,
        replenishment_date=date(2012, 1, 1),
        is_synthetic=True,
        available_stock=98,
    )

    mapping = RewardProductMapping(
        reward_id="REWARD-001",
        product_id="PROD-001",
        minimum_stock_required=2,
        inventory_constraint_type="HARD",
        is_synthetic=True,
    )

    approval = RewardApproval(
        approval_id="APPROVAL-001",
        idempotency_key="approval-key-001",
        request_hash="approval-hash",
        customer_id=12347,
        reward_id="REWARD-001",
        campaign_id="CAMP-001",
        purchase_value=Decimal("1000"),
        evaluation_date=date(2011, 12, 10),
        points_required=1718,
        reward_cost=Decimal("1730"),
        approval_status="APPROVED",
        created_at=datetime(2011, 12, 10),
    )

    session.add_all([
        customer,
        campaign,
        reward,
        inventory,
        mapping,
        approval,
    ])
    session.commit()

    yield session

    session.close()
    engine.dispose()


@pytest.fixture
def redemption_request():
    return SimpleNamespace(
        approval_id="APPROVAL-001",
        customer_id=12347,
        reward_id="REWARD-001",
        campaign_id="CAMP-001",
        idempotency_key="redemption-key-001",
    )


def test_successful_redemption(db, redemption_request):
    result = redeem_reward(db, redemption_request)

    customer = db.query(CustomerLoyaltyProfile).first()
    campaign = db.query(CampaignBudget).first()
    inventory = db.query(InventorySnapshot).first()
    approval = db.query(RewardApproval).first()

    assert result.redemption_status == "REDEEMED"
    assert customer.points_balance == 3282
    assert campaign.approved_amount == Decimal("0")
    assert campaign.committed_amount == Decimal("6730")
    assert inventory.on_hand_stock == 98
    assert inventory.reserved_stock == 0
    assert inventory.available_stock == 98
    assert approval.approval_status == "REDEEMED"


def test_duplicate_redemption(db, redemption_request):
    first = redeem_reward(db, redemption_request)
    second = redeem_reward(db, redemption_request)

    assert first.redemption_id == second.redemption_id
    assert db.query(RewardLedger).count() == 1


def test_different_request_same_key(db, redemption_request):
    redeem_reward(db, redemption_request)

    redemption_request.customer_id = 99999

    with pytest.raises(
        ValueError,
        match="Idempotency key already used with different request",
    ):
        redeem_reward(db, redemption_request)

    assert db.query(RewardLedger).count() == 1


def test_insufficient_points(db, redemption_request):
    customer = db.query(CustomerLoyaltyProfile).first()
    customer.points_balance = 100
    db.commit()

    with pytest.raises(ValueError, match="Insufficient points balance"):
        redeem_reward(db, redemption_request)

    assert customer.points_balance == 100
    assert db.query(RewardLedger).count() == 0


def test_insufficient_approved_budget(db, redemption_request):
    campaign = db.query(CampaignBudget).first()
    campaign.approved_amount = Decimal("100")
    db.commit()

    with pytest.raises(
        ValueError,
        match="Approved campaign amount is insufficient",
    ):
        redeem_reward(db, redemption_request)

    assert campaign.approved_amount == Decimal("100")
    assert campaign.committed_amount == Decimal("5000")
    assert db.query(RewardLedger).count() == 0
