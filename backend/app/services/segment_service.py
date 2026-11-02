
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[3]

SEGMENT_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "customer_rfm_segments.csv"
)


def get_customer_segment(customer_id: int):

    df = pd.read_csv(SEGMENT_FILE)

    customer = df[
        df["customer_id"] == customer_id
    ]

    if customer.empty:
        return None

    record = customer.iloc[0]

    return {
        "customer_id": int(record["customer_id"]),
        "recency": int(record["recency"]),
        "frequency": int(record["frequency"]),
        "monetary": float(record["monetary"]),
        "cluster": int(record["cluster"])
    }
