from app.db import SessionLocal
from app.models import User
from app.auth.utils import hash_password

db = SessionLocal()

users = db.query(User).all()

for user in users:
    # ONLY re-hash if password is NOT bcrypt
    if not user.password.startswith("$2b$"):
        print(f"🔑 Rehashing password for {user.username}")
        user.password = hash_password(user.password)

db.commit()
db.close()

print("✅ Passwords fixed successfully")
