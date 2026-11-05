import os

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL .env file mein nahi mila")

engine = create_engine(DATABASE_URL)

DATA_DIR = "data/processed/synthetic"

tables = [
    "customer_loyalty_profiles",
    "campaign_budgets",
    "inventory_snapshot",
    "reward_catalogue",
    "reward_product_mapping",
    "reward_ledger"
]

# Date columns that need conversion
date_columns = {
    "customer_loyalty_profiles": {
        "profile_created_at": "datetime"
    },
    "inventory_snapshot": {
        "replenishment_date": "date",
        "inventory_updated_at": "datetime"
    },
    "reward_catalogue": {
        "valid_from": "date",
        "valid_until": "date"
    },
    "reward_ledger": {
        "created_at": "datetime"
    }
}

for table in tables:

    file_path = os.path.join(DATA_DIR, f"{table}.csv")
    df = pd.read_csv(file_path)

    # Convert customer IDs into integers
    if table == "customer_loyalty_profiles":
        df["customer_id"] = df["customer_id"].astype("int64")

    # Convert date columns into proper Python date/datetime objects
    for column, date_type in date_columns.get(table, {}).items():

        if date_type == "datetime":
            df[column] = pd.to_datetime(
                df[column], errors="coerce"
            )

        elif date_type == "date":
            df[column] = pd.to_datetime(
                df[column], errors="coerce"
            ).dt.date

    print(f"\nUploading: {table}")
    print("Rows:", len(df))

    if not df.empty:
        df.to_sql(
            name=table,
            con=engine,
            if_exists="append",
            index=False,
            chunksize=1000
        )

    print(f"{table} uploaded successfully!")

print("\nAll CSV files processed successfully!")

engine.dispose()