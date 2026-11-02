
from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class CustomerLoyaltyProfile(Base):
    __tablename__ = "customer_loyalty_profiles"

    customer_id = Column(Numeric(12, 0), primary_key=True)
    loyalty_tier = Column(String, nullable=False)
    points_balance = Column(Integer, nullable=False)
    profile_status = Column(String, nullable=False)
    profile_created_at = Column(DateTime, nullable=True)
    is_synthetic = Column(Boolean, nullable=False)


class CampaignBudget(Base):
    __tablename__ = "campaign_budgets"

    campaign_id = Column(String, primary_key=True)
    budget_limit = Column(Numeric, nullable=False)
    committed_amount = Column(Numeric, nullable=False)
    approved_amount = Column(Numeric, nullable=False)
    campaign_status = Column(String, nullable=False)
    is_synthetic = Column(Boolean, nullable=False)
    available_budget_before_approval = Column(Numeric, nullable=False)


class InventorySnapshot(Base):
    __tablename__ = "inventory_snapshot"

    product_id = Column(String, primary_key=True)
    on_hand_stock = Column(Integer, nullable=False)
    reserved_stock = Column(Integer, nullable=False)
    reorder_level = Column(Integer, nullable=False)
    replenishment_date = Column(Date, nullable=True)
    inventory_updated_at = Column(DateTime, nullable=True)
    is_synthetic = Column(Boolean, nullable=False)
    available_stock = Column(Integer, nullable=False)


class RewardCatalogue(Base):
    __tablename__ = "reward_catalogue"

    reward_id = Column(String, primary_key=True)
    reward_name = Column(String, nullable=False)
    reward_type = Column(String, nullable=False)
    reward_value = Column(Numeric, nullable=False)
    points_required = Column(Integer, nullable=False)
    eligible_tiers = Column(Text, nullable=False)
    valid_from = Column(Date, nullable=False)
    valid_until = Column(Date, nullable=False)
    minimum_purchase_value = Column(Numeric, nullable=True)
    status = Column(String, nullable=False)
    campaign_id = Column(
        String,
        ForeignKey("campaign_budgets.campaign_id"),
        nullable=False
    )
    is_synthetic = Column(Boolean, nullable=False)


class RewardProductMapping(Base):
    __tablename__ = "reward_product_mapping"

    reward_id = Column(
        String,
        ForeignKey("reward_catalogue.reward_id"),
        primary_key=True
    )
    product_id = Column(
        String,
        ForeignKey("inventory_snapshot.product_id"),
        primary_key=True
    )
    minimum_stock_required = Column(Integer, nullable=False)
    inventory_constraint_type = Column(String, nullable=False)
    is_synthetic = Column(Boolean, nullable=False)


class RewardLedger(Base):
    __tablename__ = "reward_ledger"

    redemption_id = Column(String, primary_key=True)
    idempotency_key = Column(String, nullable=False)
    request_hash = Column(String, nullable=False)
    customer_id = Column(
        Numeric(12, 0),
        ForeignKey("customer_loyalty_profiles.customer_id"),
        nullable=False
    )
    reward_id = Column(
        String,
        ForeignKey("reward_catalogue.reward_id"),
        nullable=False
    )
    campaign_id = Column(
        String,
        ForeignKey("campaign_budgets.campaign_id"),
        nullable=False
    )
    points_debited = Column(Integer, nullable=False)
    reward_cost = Column(Numeric, nullable=False)
    redemption_status = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=False)
    is_synthetic = Column(Boolean, nullable=False)
