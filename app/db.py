# app/db.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os

# Path to sqlite file (relative to project root)
DB_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
DB_PATH = os.path.join(DB_DIR, "app.db")
SQLALCHEMY_DATABASE_URL = f"sqlite:///{DB_PATH}"

# Ensure folder exists
os.makedirs(DB_DIR, exist_ok=True)


engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


Base = declarative_base()

def init_db():
   
    from app import models  # noqa: F401
    Base.metadata.create_all(bind=engine)
