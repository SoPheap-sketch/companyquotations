from app.db import SessionLocal
from app.models import User
from app.auth.utils import hash_password

db = SessionLocal()

username = "Sopheap"
password = "sopheap123"

# this code for check the existing user 
existing = db.query(User).filter(User.username == username).first()
if existing:
    print(f"⚠️ User '{username}' already exists")
    db.close()
    exit()
user = User(
    username=username,
    password=hash_password(password),
    is_admin=False 
)
db.add(user)
db.commit()
db.close()
print("✅ User created successfully")
print("Username:", username)
print("Password:",password)