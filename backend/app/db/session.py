
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from backend.app.config import DATABASE_URL
from backend.app.db.models import Base

clean_db_url = DATABASE_URL
if clean_db_url and clean_db_url.startswith("postgres://"):
    clean_db_url = clean_db_url.replace("postgres://", "postgresql://", 1)

# Create database engine
engine = create_engine(
    clean_db_url,
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