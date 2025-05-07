# app/db/database.py
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings # Import the global settings

# SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL
# For SQLite, a relative path like "sqlite:///./stock_api.db" means the DB file
# will be created in the root directory where you run uvicorn.

engine = create_engine(
    settings.DATABASE_URL,
    # connect_args are specifically for SQLite to allow multiple threads (FastAPI runs in threads)
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}
)

# Each instance of SessionLocal will be a database session.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for our ORM models to inherit from
Base = declarative_base()

# Dependency to get a DB session in path operations
def get_db():
    db = SessionLocal()
    try:
        yield db  # Provides the session to the path operation function
    finally:
        db.close() # Closes the session after the request is finished