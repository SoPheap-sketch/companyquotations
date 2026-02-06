from app.db import SessionLocal
from app.models import User
from app.auth.utils import hash_password

db = SessionLocal()

users = [

    # ===== CEO =====
    User(
        username="ueno.ceo",
        password=hash_password("Temp@123"),
        # Temp*123
        role="ceo",
        department="Management",
        job_title="CEO",
        is_admin=True,
        is_active=True,
        force_password_change=True
    ),
    User(
        username="hayano.ceo",
        password=hash_password("Temp@123"),
        role="ceo",
        department="Management",
        job_title="CEO",
        is_admin=True,
        is_active=True,
        force_password_change=True
    ),

    # ===== Manager =====
    User(
        username="hornlay.mgr",
        password=hash_password("Temp@123"),
        role="manager",
        department="Management",
        job_title="Project Manager",
        is_admin=False,
        is_active=True,
        force_password_change=True
    ),

    # ===== Admin (You) =====
    User(
        username="sopheap.admin",
        password=hash_password("YourSecurePassword"),
        role="admin",
        department="IT",
        job_title="Technical Interpreter & IT Engineer",
        is_admin=True,
        is_active=True,
        force_password_change=False
    ),

    # ===== Staff =====
    User(
        username="bunrak.staff",
        password=hash_password("Temp@123"),
        role="staff",
        department="Design",
        job_title="Designer",
        is_active=True,
        force_password_change=True
    ),
    User(
        username="mangleang.staff",
        password=hash_password("Temp@123"),
        role="staff",
        department="Architecture",
        job_title="Architect",
        is_active=True,
        force_password_change=True
    ),
    User(
        username="sophea.staff",
        password=hash_password("Temp@123"),
        role="staff",
        department="Architecture",
        job_title="Architect",
        is_active=True,
        force_password_change=True
    ),
]

db.add_all(users)
db.commit()
db.close()

print("✅ Users created successfully")
