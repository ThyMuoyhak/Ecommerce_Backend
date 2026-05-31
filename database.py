import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from config import settings

# Get DATABASE_URL from environment variable
DATABASE_URL = os.getenv("DATABASE_URL", settings.DATABASE_URL)

print(f"DATABASE_URL: {DATABASE_URL[:60]}..." if DATABASE_URL else "No DATABASE_URL found")

# For Render PostgreSQL (internal connection - no SSL needed)
if DATABASE_URL and "postgres" in DATABASE_URL:
    engine = create_engine(
        DATABASE_URL,
        pool_size=5,
        max_overflow=10,
        pool_timeout=30,
        pool_recycle=1800,
        pool_pre_ping=True,
    )
    print("PostgreSQL engine created (internal connection)")
elif DATABASE_URL and "sqlite" in DATABASE_URL:
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False}
    )
    print("SQLite engine created")
else:
    raise ValueError(f"Unsupported database URL")

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()