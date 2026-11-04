
"""
MCP Server
Exposes approved read-only tools for the Loyalty Reward System.
"""

from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

import pandas as pd
from fastmcp import FastMCP

from backend.app.db.models import RewardProductMapping, RewardCatalogue
from backend.app.db.models import RewardProductMapping
from backend.app.db.repositories.campaign_repository import get_campaign_by_id
from backend.app.db.repositories.customer_repository import get_customer_by_id
from backend.app.db.repositories.inventory_repository import (
    get_product_inventory as fetch_product_inventory,
)
from backend.app.db.repositories.reward_repository import get_reward_by_id
from backend.app.db.session import SessionLocal

mcp = FastMCP("LoyaltyRewardMCP")

BASE_DIR = Path(__file__).resolve().parents[3]

TRANSACTION_FILE = (
    BASE_DIR / "data" / "interim" / "cleaned_transactions.csv"
)


def serialize_value(value):
    """Convert database values into JSON-compatible values."""

    if isinstance(value, Decimal):
        return float(value)

    if isinstance(value, (date, datetime)):
        return value.isoformat()

    return value


def serialize_record(record, fields):
    """Convert selected ORM fields into a dictionary."""

    return {
        field: serialize_value(getattr(record, field))
        for field in fields
    }


@mcp.tool
def get_customer_profile(customer_id: int) -> dict:
    """Retrieve a customer's loyalty profile."""

    db = SessionLocal()

    try:
        customer = get_customer_by_id(db, customer_id)

        if customer is None:
            return {
                "status": "NOT_FOUND",
                "data": None
            }

        fields = [
            "customer_id",
            "loyalty_tier",
            "points_balance",
            "profile_status",
            "profile_created_at",
            "is_synthetic"
        ]

        return {
            "status": "SUCCESS",
            "data": serialize_record(customer, fields)
        }

    except Exception as error:
        return {
            "status": "DATABASE_ERROR",
            "error": str(error),
            "data": None
        }

    finally:
        db.close()


@mcp.tool
def get_transaction_history(
    customer_id: int,
    limit: int = 20
) -> dict:
    """Retrieve recent customer transactions from the CSV dataset."""

    if limit < 1 or limit > 100:
        return {
            "status": "INVALID_LIMIT",
            "data": []
        }

    if not TRANSACTION_FILE.exists():
        return {
            "status": "DATASET_NOT_FOUND",
            "data": []
        }

    try:
        transactions = []
        customer_column = None

        for chunk in pd.read_csv(
            TRANSACTION_FILE,
            chunksize=50000
        ):

            if customer_column is None:

                column_map = {
                    str(column).strip().lower().replace(" ", "").replace("_", ""): column
                    for column in chunk.columns
                }

                customer_column = column_map.get("customerid")

                if customer_column is None:
                    return {
                        "status": "INVALID_DATASET_SCHEMA",
                        "data": []
                    }

            matching_rows = chunk[
                pd.to_numeric(
                    chunk[customer_column],
                    errors="coerce"
                ) == customer_id
            ]

            if not matching_rows.empty:
                transactions.extend(
                    matching_rows.to_dict(orient="records")
                )

        transactions = transactions[-limit:]

        serialized_transactions = []

        for row in transactions:
            serialized_row = {}

            for key, value in row.items():

                if pd.isna(value):
                    serialized_row[str(key)] = None
                else:
                    serialized_row[str(key)] = serialize_value(value)

            serialized_transactions.append(serialized_row)

        return {
            "status": "SUCCESS",
            "data": serialized_transactions
        }

    except Exception as error:
        return {
            "status": "DATA_ERROR",
            "error": str(error),
            "data": []
        }


@mcp.tool
def get_product_inventory(product_id: str) -> dict:
    """Retrieve stock and replenishment information for a product."""

    db = SessionLocal()

    try:
        inventory = fetch_product_inventory(db, product_id)

        if inventory is None:
            return {
                "status": "NOT_FOUND",
                "data": None
            }

        fields = [
            "product_id",
            "on_hand_stock",
            "reserved_stock",
            "reorder_level",
            "replenishment_date",
            "available_stock",
            "inventory_updated_at"
        ]

        return {
            "status": "SUCCESS",
            "data": serialize_record(inventory, fields)
        }

    except Exception as error:
        return {
            "status": "DATABASE_ERROR",
            "error": str(error),
            "data": None
        }

    finally:
        db.close()


@mcp.tool
def get_campaign_details(campaign_id: str) -> dict:
    """Retrieve campaign status and budget information."""

    db = SessionLocal()

    try:
        campaign = get_campaign_by_id(db, campaign_id)

        if campaign is None:
            return {
                "status": "NOT_FOUND",
                "data": None
            }

        fields = [
            "campaign_id",
            "budget_limit",
            "committed_amount",
            "approved_amount",
            "campaign_status",
            "available_budget_before_approval"
        ]

        return {
            "status": "SUCCESS",
            "data": serialize_record(campaign, fields)
        }

    except Exception as error:
        return {
            "status": "DATABASE_ERROR",
            "error": str(error),
            "data": None
        }

    finally:
        db.close()


@mcp.tool
def get_reward_details(reward_id: str) -> dict:
    """Retrieve reward catalogue information."""

    db = SessionLocal()

    try:
        reward = get_reward_by_id(db, reward_id)

        if reward is None:
            return {
                "status": "NOT_FOUND",
                "data": None
            }

        fields = [
            "reward_id",
            "reward_name",
            "reward_type",
            "reward_value",
            "points_required",
            "eligible_tiers",
            "valid_from",
            "valid_until",
            "minimum_purchase_value",
            "status",
            "campaign_id"
        ]

        return {
            "status": "SUCCESS",
            "data": serialize_record(reward, fields)
        }

    except Exception as error:
        return {
            "status": "DATABASE_ERROR",
            "error": str(error),
            "data": None
        }

    finally:
        db.close()

@mcp.tool
def get_reward_product_mappings(reward_id: str):
    """
    Get all product mappings linked to a reward.
    Returns product IDs and their inventory requirements.
    """

    if not reward_id or not reward_id.strip():
        return {
            "status": "INVALID_REWARD_ID",
            "data": []
        }

    db = SessionLocal()

    try:
        mappings = (
            db.query(RewardProductMapping)
            .filter(
                RewardProductMapping.reward_id == reward_id
            )
            .all()
        )

        mapping_data = [
            {
                "reward_id": mapping.reward_id,
                "product_id": mapping.product_id,
                "minimum_stock_required": mapping.minimum_stock_required,
                "inventory_constraint_type": mapping.inventory_constraint_type
            }
            for mapping in mappings
        ]

        return {
            "status": "SUCCESS",
            "data": mapping_data
        }

    except Exception as error:
        return {
            "status": "DATABASE_ERROR",
            "error": str(error),
            "data": []
        }

    finally:
        db.close()

@mcp.tool
def get_active_rewards() -> dict:
    """
    Retrieve all active rewards from the reward catalogue.
    """

    db = SessionLocal()

    try:
        rewards = (
            db.query(RewardCatalogue)
            .filter(RewardCatalogue.status == "active")
            .all()
        )

        fields = [
            "reward_id",
            "reward_name",
            "reward_type",
            "reward_value",
            "points_required",
            "eligible_tiers",
            "valid_from",
            "valid_until",
            "minimum_purchase_value",
            "status",
            "campaign_id",
            "is_synthetic"
        ]

        reward_data = [
            serialize_record(reward, fields)
            for reward in rewards
        ]

        return {
            "status": "SUCCESS",
            "data": reward_data
        }

    except Exception as error:
        return {
            "status": "DATABASE_ERROR",
            "error": str(error),
            "data": []
        }

    finally:
        db.close()


if __name__ == "__main__":
    mcp.run()
