from app.db import SessionLocal
from app.models import User
from app.auth.utils import hash_password

USERNAME = "sopheap.admin"
NEW_PASSWORD = "Sopheap@123"  # ← change this

db = SessionLocal()
try:
    user = db.query(User).filter(User.username == USERNAME).first()
    if not user:
        print("❌ User not found")
    else:
        user.password = hash_password(NEW_PASSWORD)
        user.force_password_change = False
        db.commit()
        print("✅ Password updated successfully")
finally:
    db.close()
