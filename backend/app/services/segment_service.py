from pathlib import Path
import pandas as pd
from backend.app.db.models import CustomerRFMSegment
from backend.app.db.session import SessionLocal

PROJECT_ROOT = Path(__file__).resolve().parents[3]

SEGMENT_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "customer_rfm_segments.csv"
)


def get_customer_segment(customer_id: int):
    # 1. Try querying Neon PostgreSQL database first
    db = None
    try:
        db = SessionLocal()
        record = (
            db.query(CustomerRFMSegment)
            .filter(CustomerRFMSegment.customer_id == int(customer_id))
            .first()
        )
        if record:
            return {
                "customer_id": int(record.customer_id),
                "recency": int(record.recency),
                "frequency": int(record.frequency),
                "monetary": float(record.monetary),
                "cluster": int(record.cluster),
            }
    except Exception:
        pass
    finally:
        if db:
            db.close()

    # 2. Fallback to local CSV if file exists
    if SEGMENT_FILE.exists():
        try:
            df = pd.read_csv(SEGMENT_FILE)
            customer = df[df["customer_id"] == customer_id]
            if not customer.empty:
                rec = customer.iloc[0]
                return {
                    "customer_id": int(rec["customer_id"]),
                    "recency": int(rec["recency"]),
                    "frequency": int(rec["frequency"]),
                    "monetary": float(rec["monetary"]),
                    "cluster": int(rec["cluster"]),
                }
        except Exception:
            pass

    return None
