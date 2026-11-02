
from datetime import date
from decimal import Decimal
from types import SimpleNamespace

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.db.models import (
    Base,
    CustomerLoyaltyProfile,
    RewardCatalogue,
    CampaignBudget,
    InventorySnapshot,
    RewardProductMapping,
    RewardApproval,
)
from backend.app.services.approval_service import approve_reward


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
        customer, campaign, reward, inventory, mapping
    ])
    session.commit()

    yield session

    session.close()
    engine.dispose()


@pytest.fixture
def approval_request():
    return SimpleNamespace(
        customer_id=12347,
        reward_id="REWARD-001",
        campaign_id="CAMP-001",
        purchase_value=Decimal("1000"),
        evaluation_date=date(2011, 12, 10),
        approved=True,
        idempotency_key="approval-test-001",
    )


def test_successful_approval(db, approval_request):
    result = approve_reward(db, approval_request)

    assert result.approval_status == "APPROVED"

    campaign = db.query(CampaignBudget).first()
    inventory = db.query(InventorySnapshot).first()

    assert campaign.approved_amount == Decimal("1730")
    assert inventory.reserved_stock == 2
    assert inventory.available_stock == 98


def test_duplicate_approval(db, approval_request):
    first = approve_reward(db, approval_request)
    second = approve_reward(db, approval_request)

    assert first.approval_id == second.approval_id

    assert db.query(RewardApproval).count() == 1


def test_different_request_same_key(db, approval_request):
    approve_reward(db, approval_request)

    approval_request.customer_id = 99999

    with pytest.raises(
        ValueError,
        match="Idempotency key already used with different request",
    ):
        approve_reward(db, approval_request)


def test_insufficient_budget(db, approval_request):
    campaign = db.query(CampaignBudget).first()
    campaign.budget_limit = Decimal("5000")
    db.commit()

    with pytest.raises(ValueError, match="BUDGET_EXCEEDED"):
        approve_reward(db, approval_request)

    assert db.query(RewardApproval).count() == 0
    assert campaign.approved_amount == Decimal("0")


def test_ineligible_customer(db, approval_request):
    customer = db.query(CustomerLoyaltyProfile).first()
    customer.loyalty_tier = "Bronze"
    db.commit()

    with pytest.raises(ValueError, match="TIER_NOT_ELIGIBLE"):
        approve_reward(db, approval_request)

    assert db.query(RewardApproval).count() == 0
