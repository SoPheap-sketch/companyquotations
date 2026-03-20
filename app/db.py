# # app/db.py
# from sqlalchemy import create_engine
# from sqlalchemy.orm import sessionmaker, declarative_base
# from pathlib import Path

# BASE_DIR = Path(__file__).resolve().parent.parent
# DB_PATH = BASE_DIR / "data" / "app.db"

# SQLALCHEMY_DATABASE_URL = f"sqlite:///{DB_PATH}"

# engine = create_engine(
#     SQLALCHEMY_DATABASE_URL,
#     connect_args={"check_same_thread": False}
# )

# SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
# Base = declarative_base()

# def init_db():
#     from app import models
#     Base.metadata.create_all(bind=engine, checkfirst=True)
# from sqlalchemy import create_engine
# from sqlalchemy.orm import sessionmaker, declarative_base
# import os

# DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:////tmp/app.db")

# engine = create_engine(
#     DATABASE_URL,
#     connect_args={"check_same_thread": False}
# )

# SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
# Base = declarative_base()

# def init_db():
#     from app import models
#     Base.metadata.create_all(bind=engine, checkfirst=True)
# -----3 time --------------
# from sqlalchemy import create_engine
# from sqlalchemy.orm import sessionmaker, declarative_base
# import os
# import shutil

# DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:////tmp/app.db")

# engine = create_engine(
#     DATABASE_URL,
#     connect_args={"check_same_thread": False}
# )

# SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
# Base = declarative_base()


# def init_db():
#     from app import models

#     #  COPY OLD DB INTO /tmp (ONLY FIRST TIME)
#     if not os.path.exists("/tmp/app.db"):
#         if os.path.exists("data/app.db"):
#             shutil.copy("data/app.db", "/tmp/app.db")

#     Base.metadata.create_all(bind=engine, checkfirst=True)



from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os

# 1. Find your project root
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 2. Point directly to your 'data/app.db' file
# Make sure the 'data' folder exists in your GitHub repo!
DB_PATH = os.path.join(BASE_DIR, "data", "app.db")
DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def init_db():
    from app import models
    # This will create tables if they are missing but WON'T delete your old data
    Base.metadata.create_all(bind=engine, checkfirst=True)