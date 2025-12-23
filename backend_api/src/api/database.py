import os
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, Session

# Read database URL from environment with a sensible default placeholder.
# IMPORTANT: The orchestrator should set DATABASE_URL in the container .env file.
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://postgres:postgres@localhost:5432/postgres",
)

# Create engine and session maker
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

Base = declarative_base()


# PUBLIC_INTERFACE
def get_db() -> Generator[Session, None, None]:
    """Yield a database session and ensure it is closed.

    Returns:
        Generator[Session, None, None]: SQLAlchemy session generator.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
