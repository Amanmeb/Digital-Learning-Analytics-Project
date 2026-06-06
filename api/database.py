# Manages database connection and session handling
# Used by all routers to interact with PostgreSQL

import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://cdlaid_user:CdlaidDB2025!Strong@localhost:5432/cdlaid_analytics"
)

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    # Yields a database session and closes it when done
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_db_connection():
    # Returns True if database is reachable, False otherwise
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
