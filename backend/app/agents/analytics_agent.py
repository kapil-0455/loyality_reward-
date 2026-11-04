
"""
Analytics Agent
Combines existing RFM features, K-Means segments
and customer loyalty profiles.
"""

from pathlib import Path

import pandas as pd

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
            "analytics": None
        }

    try:

        # Check whether all datasets exist
        if (
            not RFM_FILE.exists()
            or not SEGMENT_FILE.exists()
            or not LOYALTY_FILE.exists()
        ):
            return {
                "status": "DATASET_NOT_FOUND",
                "analytics": None
            }

        # Load existing datasets
        rfm_df = pd.read_csv(RFM_FILE)
        segment_df = pd.read_csv(SEGMENT_FILE)
        loyalty_df = pd.read_csv(LOYALTY_FILE)

        # Validate required columns
        if not {
            "customer_id",
            "recency",
            "frequency",
            "monetary",
            "last_purchase_date"
        }.issubset(rfm_df.columns):

            return {
                "status": "INVALID_RFM_SCHEMA",
                "analytics": None
            }

        if not {
            "customer_id",
            "cluster"
        }.issubset(segment_df.columns):

            return {
                "status": "INVALID_SEGMENT_SCHEMA",
                "analytics": None
            }

        if not {
            "customer_id",
            "loyalty_tier",
            "points_balance"
        }.issubset(loyalty_df.columns):

            return {
                "status": "INVALID_LOYALTY_SCHEMA",
                "analytics": None
            }

        # Normalize customer IDs before joining
        for df in [rfm_df, segment_df, loyalty_df]:

            df["customer_id"] = df["customer_id"].apply(
                normalize_customer_id
            )

        customer_id = normalize_customer_id(customer_id)

        # Prevent ambiguous customer records
        if (
            rfm_df["customer_id"].duplicated().any()
            or segment_df["customer_id"].duplicated().any()
            or loyalty_df["customer_id"].duplicated().any()
        ):

            return {
                "status": "DUPLICATE_CUSTOMER_DATA",
                "analytics": None
            }

        # Select the requested customer's records
        rfm = rfm_df[
            rfm_df["customer_id"] == customer_id
        ]

        segment = segment_df[
            segment_df["customer_id"] == customer_id
        ]

        loyalty = loyalty_df[
            loyalty_df["customer_id"] == customer_id
        ]

        if rfm.empty or segment.empty or loyalty.empty:

            return {
                "status": "CUSTOMER_DATA_NOT_FOUND",
                "analytics": None
            }

        # Combine RFM and segment datasets
        analytics_df = rfm.merge(
            segment[["customer_id", "cluster"]],
            on="customer_id",
            validate="one_to_one"
        )

        # Combine with loyalty profiles
        analytics_df = analytics_df.merge(
            loyalty,
            on="customer_id",
            validate="one_to_one"
        )

        # Convert missing values to None
        analytics = {
            key: None if pd.isna(value) else value
            for key, value in analytics_df.iloc[0].to_dict().items()
        }

        return {
            "status": "SUCCESS",
            "customer_id": customer_id,
            "analytics": analytics
        }

    except Exception as error:  # noqa: BLE001

        return {
            "status": "ANALYTICS_ERROR",
            "error": str(error),
            "analytics": None
        }
