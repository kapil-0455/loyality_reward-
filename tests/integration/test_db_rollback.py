from datetime import date, datetime
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import patch

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
    RewardLedger,
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


def test_approval_rollback_on_business_rule_failure(db):
    """When approval fails eligibility, rollback ensures no approval record and no resource allocation."""
    request = SimpleNamespace(
        customer_id=12347,
        reward_id="REWARD-001",
        campaign_id="CAMP-001",
        purchase_value=Decimal("10"),  # Below minimum purchase of 500
        evaluation_date=date(2011, 12, 10),
        approved=True,
        idempotency_key="rollback-approval-minpurchase",
    )

    with pytest.raises(ValueError, match="MINIMUM_PURCHASE_NOT_MET"):
        approve_reward(db, request)

    # Database state must be clean and unmutated
    approvals = db.query(RewardApproval).all()
    assert len(approvals) == 0

    campaign = db.query(CampaignBudget).filter_by(campaign_id="CAMP-001").first()
    assert campaign.approved_amount == Decimal("0")

    inventory = db.query(InventorySnapshot).filter_by(product_id="PROD-001").first()
    assert inventory.reserved_stock == 0


def test_approval_rollback_on_unexpected_database_commit_error(db):
    """If database commit fails during approval, session rolls back cleanly."""
    request = SimpleNamespace(
        customer_id=12347,
        reward_id="REWARD-001",
        campaign_id="CAMP-001",
        purchase_value=Decimal("1000"),
        evaluation_date=date(2011, 12, 10),
        approved=True,
        idempotency_key="rollback-commit-fail",
    )

    with patch.object(db, "commit", side_effect=RuntimeError("Simulated DB commit error")):
        with pytest.raises(RuntimeError, match="Simulated DB commit error"):
            approve_reward(db, request)

    # Verify no approval persisted
    approvals = db.query(RewardApproval).filter_by(idempotency_key="rollback-commit-fail").all()
    assert len(approvals) == 0


def test_redemption_rollback_on_unexpected_failure(db):
    """If redemption crashes during transaction, customer points and inventory remain uncorrupted."""
    # 1. Create a valid approval first
    approval_request = SimpleNamespace(
        customer_id=12347,
        reward_id="REWARD-001",
        campaign_id="CAMP-001",
        purchase_value=Decimal("1000"),
        evaluation_date=date(2011, 12, 10),
        approved=True,
        idempotency_key="approval-pre-redemption",
    )
    approval = approve_reward(db, approval_request)
    assert approval.approval_status == "APPROVED"

    initial_points = 5000
    initial_on_hand = 100

    redemption_request = SimpleNamespace(
        approval_id=approval.approval_id,
        customer_id=12347,
        reward_id="REWARD-001",
        campaign_id="CAMP-001",
        idempotency_key="rollback-redemption-fail",
    )

    # Simulate crash right before commit
    with patch.object(db, "commit", side_effect=RuntimeError("Simulated redemption DB commit crash")):
        with pytest.raises(RuntimeError, match="Simulated redemption DB commit crash"):
            redeem_reward(db, redemption_request)

    # 2. Verify state was rolled back completely
    # Customer points must still be 5000
    customer = db.query(CustomerLoyaltyProfile).filter_by(customer_id=12347).first()
    assert customer.points_balance == initial_points

    # Approval must still be APPROVED (not corrupted to REDEEMED)
    reloaded_approval = db.query(RewardApproval).filter_by(approval_id=approval.approval_id).first()
    assert reloaded_approval.approval_status == "APPROVED"

    # No ledger entry should exist
    ledgers = db.query(RewardLedger).filter_by(idempotency_key="rollback-redemption-fail").all()
    assert len(ledgers) == 0

    # Inventory on hand should still be 100
    inventory = db.query(InventorySnapshot).filter_by(product_id="PROD-001").first()
    assert inventory.on_hand_stock == initial_on_hand

