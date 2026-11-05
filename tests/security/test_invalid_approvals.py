from datetime import date, datetime
from decimal import Decimal
from types import SimpleNamespace

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.db.models import (
    Base,
    CampaignBudget,
    CustomerLoyaltyProfile,
    InventorySnapshot,
    RewardApproval,
    RewardCatalogue,
    RewardProductMapping,
)
from backend.app.services.approval_service import approve_reward
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

    session.add_all([customer, campaign, reward, inventory, mapping])
    session.commit()

    yield session

    session.close()
    engine.dispose()


def test_rejected_approval_does_not_reserve_budget_or_inventory(db):
    """When manager rejects an approval (approved=False), status is REJECTED and no resources are reserved."""
    request = SimpleNamespace(
        customer_id=12347,
        reward_id="REWARD-001",
        campaign_id="CAMP-001",
        purchase_value=Decimal("1000"),
        evaluation_date=date(2011, 12, 10),
        approved=False,
        idempotency_key="rejected-approval-001",
    )

    result = approve_reward(db, request)

    assert result.approval_status == "REJECTED"

    campaign = db.query(CampaignBudget).filter_by(campaign_id="CAMP-001").first()
    assert campaign.approved_amount == Decimal("0")

    inventory = db.query(InventorySnapshot).filter_by(product_id="PROD-001").first()
    assert inventory.reserved_stock == 0


def test_rejected_approval_cannot_be_redeemed(db):
    """Attempting to redeem a REJECTED approval must fail with 400 ValueError."""
    # 1. Create rejected approval
    approval_request = SimpleNamespace(
        customer_id=12347,
        reward_id="REWARD-001",
        campaign_id="CAMP-001",
        purchase_value=Decimal("1000"),
        evaluation_date=date(2011, 12, 10),
        approved=False,
        idempotency_key="rejected-approval-002",
    )
    rejected_approval = approve_reward(db, approval_request)
    assert rejected_approval.approval_status == "REJECTED"

    # 2. Attempt redemption
    redemption_request = SimpleNamespace(
        approval_id=rejected_approval.approval_id,
        customer_id=12347,
        reward_id="REWARD-001",
        campaign_id="CAMP-001",
        idempotency_key="redemption-reject-001",
    )

    with pytest.raises(ValueError, match="Approval is not available for redemption"):
        redeem_reward(db, redemption_request)


def test_approval_idempotency_tampering_rejected(db):
    """Reusing an idempotency key with modified parameters (tampering) is detected and rejected."""
    original_request = SimpleNamespace(
        customer_id=12347,
        reward_id="REWARD-001",
        campaign_id="CAMP-001",
        purchase_value=Decimal("1000"),
        evaluation_date=date(2011, 12, 10),
        approved=True,
        idempotency_key="tamper-key-001",
    )
    approve_reward(db, original_request)

    # Tampered request: changed purchase_value with identical idempotency_key
    tampered_request = SimpleNamespace(
        customer_id=12347,
        reward_id="REWARD-001",
        campaign_id="CAMP-001",
        purchase_value=Decimal("5000"),
        evaluation_date=date(2011, 12, 10),
        approved=True,
        idempotency_key="tamper-key-001",
    )

    with pytest.raises(
        ValueError, match="Idempotency key already used with different request"
    ):
        approve_reward(db, tampered_request)


def test_redemption_tampering_mismatched_customer(db):
    """Redemption request passing a different customer_id than the approval must be rejected."""
    # Create valid approval for customer 12347
    approval_request = SimpleNamespace(
        customer_id=12347,
        reward_id="REWARD-001",
        campaign_id="CAMP-001",
        purchase_value=Decimal("1000"),
        evaluation_date=date(2011, 12, 10),
        approved=True,
        idempotency_key="approval-valid-cust-001",
    )
    approval = approve_reward(db, approval_request)

    # Tampered redemption with customer_id 99999
    tampered_redemption = SimpleNamespace(
        approval_id=approval.approval_id,
        customer_id=99999,
        reward_id="REWARD-001",
        campaign_id="CAMP-001",
        idempotency_key="redemption-tamper-cust-001",
    )

    with pytest.raises(ValueError, match="Request does not match approval"):
        redeem_reward(db, tampered_redemption)


def test_redemption_tampering_mismatched_reward(db):
    """Redemption request passing a different reward_id than the approval must be rejected."""
    approval_request = SimpleNamespace(
        customer_id=12347,
        reward_id="REWARD-001",
        campaign_id="CAMP-001",
        purchase_value=Decimal("1000"),
        evaluation_date=date(2011, 12, 10),
        approved=True,
        idempotency_key="approval-valid-rew-001",
    )
    approval = approve_reward(db, approval_request)

    tampered_redemption = SimpleNamespace(
        approval_id=approval.approval_id,
        customer_id=12347,
        reward_id="REWARD-DIFFERENT",
        campaign_id="CAMP-001",
        idempotency_key="redemption-tamper-rew-001",
    )

    with pytest.raises(ValueError, match="Request does not match approval"):
        redeem_reward(db, tampered_redemption)


def test_redemption_tampering_mismatched_campaign(db):
    """Redemption request passing a different campaign_id than the approval must be rejected."""
    approval_request = SimpleNamespace(
        customer_id=12347,
        reward_id="REWARD-001",
        campaign_id="CAMP-001",
        purchase_value=Decimal("1000"),
        evaluation_date=date(2011, 12, 10),
        approved=True,
        idempotency_key="approval-valid-camp-001",
    )
    approval = approve_reward(db, approval_request)

    tampered_redemption = SimpleNamespace(
        approval_id=approval.approval_id,
        customer_id=12347,
        reward_id="REWARD-001",
        campaign_id="CAMP-DIFFERENT",
        idempotency_key="redemption-tamper-camp-001",
    )

    with pytest.raises(ValueError, match="Request does not match approval"):
        redeem_reward(db, tampered_redemption)


def test_cannot_redeem_already_redeemed_approval(db):
    """An approval that has already been successfully redeemed cannot be redeemed again."""
    approval_request = SimpleNamespace(
        customer_id=12347,
        reward_id="REWARD-001",
        campaign_id="CAMP-001",
        purchase_value=Decimal("1000"),
        evaluation_date=date(2011, 12, 10),
        approved=True,
        idempotency_key="approval-double-redeem-001",
    )
    approval = approve_reward(db, approval_request)

    # First redemption succeeds
    redemption_1 = SimpleNamespace(
        approval_id=approval.approval_id,
        customer_id=12347,
        reward_id="REWARD-001",
        campaign_id="CAMP-001",
        idempotency_key="redemption-first-001",
    )
    redeem_reward(db, redemption_1)

    # Second redemption with NEW idempotency key attempts double redemption
    redemption_2 = SimpleNamespace(
        approval_id=approval.approval_id,
        customer_id=12347,
        reward_id="REWARD-001",
        campaign_id="CAMP-001",
        idempotency_key="redemption-second-tamper-002",
    )

    with pytest.raises(ValueError, match="Approval is not available for redemption"):
        redeem_reward(db, redemption_2)


def test_approval_rejects_reward_campaign_mismatch(db):
    """Reward belonging to CAMP-001 cannot be approved under CAMP-999."""
    other_campaign = CampaignBudget(
        campaign_id="CAMP-OTHER",
        budget_limit=Decimal("50000"),
        committed_amount=Decimal("0"),
        approved_amount=Decimal("0"),
        campaign_status="active",
        is_synthetic=True,
        available_budget_before_approval=Decimal("50000"),
    )
    db.add(other_campaign)
    db.commit()

    request = SimpleNamespace(
        customer_id=12347,
        reward_id="REWARD-001",
        campaign_id="CAMP-OTHER",
        purchase_value=Decimal("1000"),
        evaluation_date=date(2011, 12, 10),
        approved=True,
        idempotency_key="mismatch-camp-001",
    )

    with pytest.raises(ValueError, match="Reward does not belong to this campaign"):
        approve_reward(db, request)

