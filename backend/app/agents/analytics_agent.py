"""
Analytics Agent
Combines existing RFM features, K-Means segments
and customer loyalty profiles via Neon PostgreSQL with local CSV fallback.
"""

from pathlib import Path
import pandas as pd

from backend.app.db.models import (
    CustomerLoyaltyProfile,
    CustomerRFMSegment,
    RFMCustomerFeature,
)
from backend.app.db.session import SessionLocal

# Project root directory
BASE_DIR = Path(__file__).resolve().parents[3]

RFM_FILE = BASE_DIR / "data" / "processed" / "rfm_customer_features.csv"
SEGMENT_FILE = BASE_DIR / "data" / "processed" / "customer_rfm_segments.csv"
LOYALTY_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "synthetic"
    / "customer_loyalty_profiles.csv"
)


def normalize_customer_id(value):
    """
    Normalize customer IDs so that values like
    12346, 12346.0 and 12346.00 match.
    """
    value = str(value).strip()
    try:
        numeric_value = float(value)
        if numeric_value.is_integer():
            return str(int(numeric_value))
    except ValueError:
        pass
    return value


def run_analytics_agent(customer_id):
    if customer_id is None:
        return {
            "status": "INVALID_CUSTOMER_ID",
            "analytics": None,
        }

    norm_id = normalize_customer_id(customer_id)
    try:
        int_id = int(norm_id)
    except ValueError:
        return {
            "status": "INVALID_CUSTOMER_ID",
            "analytics": None,
        }

    # 1. Primary: Try direct retrieval from Neon PostgreSQL Database
    db = None
    try:
        db = SessionLocal()
        loyalty = (
            db.query(CustomerLoyaltyProfile)
            .filter(CustomerLoyaltyProfile.customer_id == int_id)
            .first()
        )
        rfm = (
            db.query(RFMCustomerFeature)
            .filter(RFMCustomerFeature.customer_id == int_id)
            .first()
        )
        seg = (
            db.query(CustomerRFMSegment)
            .filter(CustomerRFMSegment.customer_id == int_id)
            .first()
        )

        if loyalty and rfm and seg:
            analytics = {
                "customer_id": norm_id,
                "recency": int(rfm.recency),
                "frequency": int(rfm.frequency),
                "monetary": float(rfm.monetary),
                "last_purchase_date": (
                    rfm.last_purchase_date.strftime("%Y-%m-%d %H:%M:%S")
                    if rfm.last_purchase_date
                    else None
                ),
                "cluster": int(seg.cluster),
                "loyalty_tier": loyalty.loyalty_tier,
                "points_balance": int(loyalty.points_balance),
                "profile_status": loyalty.profile_status,
                "profile_created_at": (
                    loyalty.profile_created_at.strftime("%Y-%m-%d %H:%M:%S")
                    if loyalty.profile_created_at
                    else None
                ),
                "is_synthetic": loyalty.is_synthetic,
            }
            return {
                "status": "SUCCESS",
                "customer_id": norm_id,
                "analytics": analytics,
            }
    except Exception:
        pass
    finally:
        if db:
            db.close()

    # 2. Fallback: Local CSV files if present
    try:
        if (
            not RFM_FILE.exists()
            or not SEGMENT_FILE.exists()
            or not LOYALTY_FILE.exists()
        ):
            return {
                "status": "DATASET_NOT_FOUND",
                "analytics": None,
            }

        rfm_df = pd.read_csv(RFM_FILE)
        segment_df = pd.read_csv(SEGMENT_FILE)
        loyalty_df = pd.read_csv(LOYALTY_FILE)

        for df in [rfm_df, segment_df, loyalty_df]:
            df["customer_id"] = df["customer_id"].apply(normalize_customer_id)

        rfm_sub = rfm_df[rfm_df["customer_id"] == norm_id]
        seg_sub = segment_df[segment_df["customer_id"] == norm_id]
        loy_sub = loyalty_df[loyalty_df["customer_id"] == norm_id]

        if rfm_sub.empty or seg_sub.empty or loy_sub.empty:
            return {
                "status": "CUSTOMER_DATA_NOT_FOUND",
                "analytics": None,
            }

        analytics_df = rfm_sub.merge(
            seg_sub[["customer_id", "cluster"]],
            on="customer_id",
            validate="one_to_one",
        )
        analytics_df = analytics_df.merge(
            loy_sub,
            on="customer_id",
            validate="one_to_one",
        )

        analytics = {
            key: None if pd.isna(val) else val
            for key, val in analytics_df.iloc[0].to_dict().items()
        }

        return {
            "status": "SUCCESS",
            "customer_id": norm_id,
            "analytics": analytics,
        }

    except Exception as error:
        return {
            "status": "ANALYTICS_ERROR",
            "error": str(error),
            "analytics": None,
        }
