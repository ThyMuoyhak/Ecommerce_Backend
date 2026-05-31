import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from config import settings

# Get DATABASE_URL from environment variable
DATABASE_URL = os.getenv("DATABASE_URL", settings.DATABASE_URL)

print(f"DATABASE_URL: {DATABASE_URL[:50]}..." if DATABASE_URL else "No DATABASE_URL found")

# Create engine - no special SSL handling needed for internal URL
if DATABASE_URL and "postgres" in DATABASE_URL:
    engine = create_engine(
        DATABASE_URL,
        pool_size=5,
        max_overflow=10,
        pool_timeout=30,
        pool_recycle=1800,
        pool_pre_ping=True,
    )
    print("PostgreSQL engine created")
elif DATABASE_URL and "sqlite" in DATABASE_URL:
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False}
    )
    print("SQLite engine created")
else:
    raise ValueError("No valid DATABASE_URL found")

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()