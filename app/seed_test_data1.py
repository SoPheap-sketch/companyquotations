from app.db import SessionLocal
from app.models import Project, Quote, QuoteItem, User
from app.auth.utils import hash_password
from datetime import datetime
import random

db = SessionLocal()
def create_users():
    users = [
        User(
            username="admin3",
            password=hash_password("admin123"),
            is_admin=True,
        ),
        User(
            username="sopheap1",
            password=hash_password("123456"),
            is_admin=False,
        ),
        User(
            username="architect1",
            password=hash_password("123456"),
            is_admin=False,
        ),
        User(
            username="designer1",
            password=hash_password("123456"),
            is_admin=False,
        ),
        User(
            username="manager1",
            password=hash_password("123456"),
            is_admin=False,
        ),
    ]

    for u in users:
        existing = db.query(User).filter(User.username == u.username).first()
        if not existing:
            db.add(u)

    db.commit()
    print(" Users created (hashed passwords)")
   
    print("🎉 Test data seeding complete")

