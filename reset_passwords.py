from app.db import SessionLocal
from app.models import User
from app.auth.utils import hash_password

db = SessionLocal()

for u in db.query(User).all():
    u.password = hash_password("123456")

db.commit()
db.close()
print("✅ All passwords reset to 123456")