from app.db import SessionLocal
from app.models import User
from app.auth.utils import hash_password

db = SessionLocal()

existing = db.query(User).filter(User.username == "admin1").first()
if existing:
    print("⚠️ Admin user already exists")
else:
    admin1 = User(
        username="admin1",
        password="admin123",
        is_admin=True
    )
    db.add(admin1)
    db.commit()
    print("✅ Admin user created")

db.close()
