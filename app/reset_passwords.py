from app.db import SessionLocal
from app.models import User
from app.auth.utils import hash_password

db = SessionLocal()
user = db.query(User).filter(User.username == "admin").first()
user.password = hash_password("admin123")
user.force_password_change = False
db.commit()
db.close()
