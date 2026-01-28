# app/fix_roles.py
from app.db import SessionLocal
from app.models import User

db = SessionLocal()

users = {
    "admin3": ("admin3", "Management", "System Administrator", True),
    "sopheap1": ("staff", "IT", "IT Engineer / Technical Interpreter", False),
    "architect1": ("staff", "Design", "Architect", False),
    "designer1": ("staff", "Design", "Designer", False),
    "manager1": ("manager", "Management", "Project Manager", False),
}

for username, (role, dept, title, is_admin) in users.items():
    u = db.query(User).filter(User.username == username).first()
    if u:
        u.role = role
        u.department = dept
        u.job_title = title      # ✅ FIXED
        u.is_admin = is_admin
        print(f"✅ Updated {username}")

db.commit()
db.close()
print("🎉 User roles updated successfully.")
