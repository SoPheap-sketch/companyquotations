from app.db import SessionLocal
from app.models import User

OLD = "mangleang.staff"
NEW = "mengleang.staff"

db = SessionLocal()
try:
    user = db.query(User).filter(User.username == OLD).first()
    if not user:
        print("❌ User not found")
    else:
        user.username = NEW
        db.commit()
        print(f"✅ Renamed {OLD} → {NEW}")
finally:
    db.close()
