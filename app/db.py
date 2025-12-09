import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Default to a local sqlite file (data/app.db)
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/app.db")

# sqlite needs check_same_thread flag
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def init_db():
    """
    Create all tables. We import models here to avoid circular imports
    when other modules import SessionLocal at top level.
    """
    # Import models only when initializing to avoid import cycles
    from app import models  # noqa: F401
    Base.metadata.create_all(bind=engine)
