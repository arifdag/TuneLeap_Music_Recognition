from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db.sql.models import Base
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get DATABASE_URL from environment variables or use default for development
DATABASE_URL = os.getenv("DATABASE_URL")

# create synchronous engine
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
)

# configure Session class
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

def get_db():
    """
    Dependency for FastAPI routes.
    Yields a SQLAlchemy Session, and ensures it is closed after use.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
