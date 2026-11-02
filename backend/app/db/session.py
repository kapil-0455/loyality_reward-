
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from backend.app.config import DATABASE_URL
from backend.app.db.models import Base

# Create database engine
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True
)

# Create database sessions
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


# Database connection test
def test_db_connection():
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            print("Database connected successfully!")
            print("Test result:", result.scalar())

    except Exception as error:
        print("Database connection failed:", error)
        raise

def init_db():
    Base.metadata.create_all(bind=engine)