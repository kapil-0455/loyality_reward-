import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# .env file se database URL load karo
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL .env file mein nahi mila")

# Database connection
engine = create_engine(DATABASE_URL)

try:
    with engine.connect() as connection:
        result = connection.execute(
            text("SELECT current_database(), current_user;")
        )

        database, user = result.fetchone()

        print("Database connected successfully!")
        print("Database:", database)
        print("User:", user)

except Exception as e:
    print("Connection failed:", e)