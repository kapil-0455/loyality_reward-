
import os
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from threading import Barrier
from uuid import uuid4
from datetime import date

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.db.models import (
    CustomerLoyaltyProfile,
    CampaignBudget,
    InventorySnapshot,
    RewardCatalogue,
    RewardProductMapping,
    RewardApproval,
)
from backend.app.api.schemas.approval import ApprovalRequest
from backend.app.services.approval_service import approve_reward


@pytest.fixture
def test_db():
    database_url = os.getenv("TEST_DATABASE_URL")

    if not database_url:
        pytest.fail("TEST_DATABASE_URL is not configured")

    engine = create_engine(
        database_url,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=5,
    )

    TestingSession = sessionmaker(
        bind=engine,
        autocommit=False,
        autoflush=False,
    )

    yield TestingSession
    engine.dispose()


def test_concurrent_approval(test_db):

    customer_id = uuid4().int % 900_000_000_000 + 100_000_000_000

    campaign_id = f"TEST-CAMP-{uuid4().hex[:10]}"
    reward_id = f"TEST-REWARD-{uuid4().hex[:10]}"
    product_id = f"TEST-PROD-{uuid4().hex[:10]}"

    idempotency_key = f"APPROVAL-{uuid4().hex}"

    seed_db = test_db()

    try:
        customer = CustomerLoyaltyProfile(
            customer_id=customer_id,
            loyalty_tier="Gold",
            points_balance=5000,
            profile_status="active",
            is_synthetic=True,
        )

        campaign = CampaignBudget(
            campaign_id=campaign_id,
            budget_limit=Decimal("5000"),
            committed_amount=Decimal("0"),
            approved_amount=Decimal("0"),
            campaign_status="active",
            is_synthetic=True,
            available_budget_before_approval=Decimal("5000"),
        )

        inventory = InventorySnapshot(
            product_id=product_id,
            on_hand_stock=20,
            reserved_stock=0,
            reorder_level=5,
            replenishment_date=date(2030, 1, 1),
            is_synthetic=True,
            available_stock=20,
        )

        seed_db.add_all([customer, campaign, inventory])
        seed_db.flush()

        reward = RewardCatalogue(
            reward_id=reward_id,
            reward_name="Concurrent Approval Test",
            reward_type="product",
            reward_value=Decimal("100"),
            points_required=500,
            eligible_tiers="Gold",
            valid_from=date(2020, 1, 1),
            valid_until=date(2035, 12, 31),
            minimum_purchase_value=Decimal("0"),
            status="active",
            campaign_id=campaign_id,
            is_synthetic=True,
        )

        seed_db.add(reward)
        seed_db.flush()

        mapping = RewardProductMapping(
            reward_id=reward_id,
            product_id=product_id,
            minimum_stock_required=2,
            inventory_constraint_type="HARD",
            is_synthetic=True,
        )

        seed_db.add(mapping)
        seed_db.commit()

    except Exception:
        seed_db.rollback()
        raise

    finally:
        seed_db.close()

    request = ApprovalRequest(
        customer_id=customer_id,
        reward_id=reward_id,
        campaign_id=campaign_id,
        purchase_value=Decimal("500"),
        evaluation_date=date.today(),
        approved=True,
        idempotency_key=idempotency_key,
    )

    worker_count = 5
    barrier = Barrier(worker_count)

    def approval_worker():
        db = test_db()

        try:
            barrier.wait()
            result = approve_reward(db, request)

            return {
                "status": "success",
                "approval_id": result.approval_id,
            }

        except Exception as error:
            return {
                "status": "error",
                "message": str(error),
            }

        finally:
            db.close()

    try:
        with ThreadPoolExecutor(max_workers=worker_count) as executor:
            results = list(
                executor.map(
                    lambda _: approval_worker(),
                    range(worker_count),
                )
            )

        print("\nConcurrent Approval Results:")
        for result in results:
            print(result)

        assert all(
            result["status"] == "success"
            for result in results
        )

        approval_ids = {
            result["approval_id"]
            for result in results
        }

        assert len(approval_ids) == 1

        verify_db = test_db()

        try:
            campaign = verify_db.query(
                CampaignBudget
            ).filter_by(campaign_id=campaign_id).one()

            inventory = verify_db.query(
                InventorySnapshot
            ).filter_by(product_id=product_id).one()

            approvals = verify_db.query(
                RewardApproval
            ).filter_by(idempotency_key=idempotency_key).all()

            assert len(approvals) == 1
            assert campaign.approved_amount == Decimal("100")
            assert inventory.reserved_stock == 2
            assert inventory.available_stock == 18

        finally:
            verify_db.close()

    finally:
        cleanup_db = test_db()

        try:
            cleanup_db.query(RewardApproval).filter_by(
                idempotency_key=idempotency_key
            ).delete(synchronize_session=False)

            cleanup_db.query(RewardProductMapping).filter_by(
                reward_id=reward_id
            ).delete(synchronize_session=False)

            cleanup_db.query(RewardCatalogue).filter_by(
                reward_id=reward_id
            ).delete(synchronize_session=False)

            cleanup_db.query(InventorySnapshot).filter_by(
                product_id=product_id
            ).delete(synchronize_session=False)

            cleanup_db.query(CampaignBudget).filter_by(
                campaign_id=campaign_id
            ).delete(synchronize_session=False)

            cleanup_db.query(CustomerLoyaltyProfile).filter_by(
                customer_id=customer_id
            ).delete(synchronize_session=False)

            cleanup_db.commit()

        except Exception:
            cleanup_db.rollback()
            raise

        finally:
            cleanup_db.close()

