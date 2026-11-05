"""
Upload RFM and Customer Segmentation tables to Neon PostgreSQL.
Centralizes analytical data alongside transactional tables.
"""

import os
from pathlib import Path
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import (
    Column,
    DateTime,
    Integer,
    Numeric,
    create_engine,
)
from sqlalchemy.orm import declarative_base

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL not found in .env file")

engine = create_engine(DATABASE_URL)
Base = declarative_base()


class CustomerRFMSegment(Base):
    __tablename__ = "customer_rfm_segments"

    customer_id = Column(Numeric(12, 0), primary_key=True)
    recency = Column(Integer, nullable=False)
    frequency = Column(Integer, nullable=False)
    monetary = Column(Numeric(12, 2), nullable=False)
    cluster = Column(Integer, nullable=False)


class RFMCustomerFeature(Base):
    __tablename__ = "rfm_customer_features"

    customer_id = Column(Numeric(12, 0), primary_key=True)
    recency = Column(Integer, nullable=False)
    frequency = Column(Integer, nullable=False)
    monetary = Column(Numeric(12, 2), nullable=False)
    last_purchase_date = Column(DateTime, nullable=True)


def upload_rfm():
    project_root = Path(__file__).resolve().parents[1]

    # Create tables in Neon DB if not present
    Base.metadata.create_all(engine)
    print("Tables customer_rfm_segments and rfm_customer_features created/verified on Neon.")

    # 1. Upload customer_rfm_segments
    seg_file = project_root / "data" / "processed" / "customer_rfm_segments.csv"
    if seg_file.exists():
        df_seg = pd.read_csv(seg_file)
        # Ensure customer_id is integer
        df_seg["customer_id"] = df_seg["customer_id"].astype(int)
        df_seg.to_sql("customer_rfm_segments", engine, if_exists="replace", index=False)
        print(f"Uploaded {len(df_seg)} rows to 'customer_rfm_segments' table on Neon.")

    # 2. Upload rfm_customer_features
    feat_file = project_root / "data" / "processed" / "rfm_customer_features.csv"
    if feat_file.exists():
        df_feat = pd.read_csv(feat_file)
        df_feat["customer_id"] = df_feat["customer_id"].astype(int)
        df_feat["last_purchase_date"] = pd.to_datetime(df_feat["last_purchase_date"])
        df_feat.to_sql("rfm_customer_features", engine, if_exists="replace", index=False)
        print(f"Uploaded {len(df_feat)} rows to 'rfm_customer_features' table on Neon.")

    print("All RFM data successfully migrated to Neon PostgreSQL!")


if __name__ == "__main__":
    upload_rfm()
