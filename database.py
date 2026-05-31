import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from config import settings

# Get DATABASE_URL from environment variable (Render provides this)
DATABASE_URL = os.getenv("DATABASE_URL", settings.DATABASE_URL)

# For Render PostgreSQL, add sslmode=require
if DATABASE_URL and "postgres" in DATABASE_URL:
    # Add sslmode=require if not already present
    if "sslmode" not in DATABASE_URL:
        if "?" in DATABASE_URL:
            DATABASE_URL += "&sslmode=require"
        else:
            DATABASE_URL += "?sslmode=require"
    print(f"Using PostgreSQL database")

# For SQLite (development)
elif DATABASE_URL and "sqlite" in DATABASE_URL:
    print(f"Using SQLite database")

# Create engine with appropriate settings
if DATABASE_URL and "postgres" in DATABASE_URL:
    engine = create_engine(
        DATABASE_URL,
        pool_size=5,  # Number of connections to keep in pool
        max_overflow=10,  # Maximum overflow connections
        pool_timeout=30,  # Timeout for getting a connection from pool
        pool_recycle=1800,  # Recycle connections after 30 minutes
        pool_pre_ping=True,  # Verify connections before using
    )
    print("PostgreSQL engine created with connection pool")
else:
    # SQLite configuration (for local development)
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
    )
    print("SQLite engine created")

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()