# app/routes/admin.py

from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from app.db import SessionLocal
from app.models import User

router = APIRouter(prefix="/admin", tags=["Admin"])
templates = Jinja2Templates(directory="app/templates")


# =========================
# ADMIN : USER LIST
# =========================
@router.get("/users")
def admin_users(request: Request):
    if request.session.get("role", "").lower() != "admin":
        raise HTTPException(status_code=403, detail="Admin access denied")

    db = SessionLocal()
    users = db.query(User).all()
    db.close()

    return templates.TemplateResponse(
        "admin_users.html",
        {
            "request": request,
            "users": users,
        }
    )


# =========================
# ADMIN : UPDATE USER
# =========================
@router.post("/users/update")
def update_user(
    request: Request,
    user_id: int = Form(...),
    role: str = Form(...),
    department: str = Form(...),
):
    if request.session.get("role", "").lower() != "admin":
        raise HTTPException(status_code=403, detail="Admin access denied")

    db = SessionLocal()
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        db.close()
        raise HTTPException(status_code=404, detail="User not found")

    # 🔒 Rule 1: cannot edit yourself (backend protection)
    if user.id == request.session.get("user_id"):
        db.close()
        raise HTTPException(status_code=400, detail="You cannot edit your own role")

    # 🔒 Rule 2: prevent removing last admin
    if user.role == "admin" and role != "admin":
        admin_count = db.query(User).filter(User.role == "admin").count()
        if admin_count <= 1:
            db.close()
            raise HTTPException(
                status_code=400,
                detail="System must have at least one admin"
            )

    # Apply updates
    user.role = role
    user.department = department
    user.is_admin = True if role == "admin" else False

    db.commit()
    db.close()

    return RedirectResponse("/admin/users", status_code=303)
# =========================
# ADMIN : CREATE USER
# =========================
@router.post("/users/create")
def create_user(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    role: str = Form(...),
    department: str = Form(...),
):
    if request.session.get("role", "").lower() != "admin":
        raise HTTPException(status_code=403, detail="Admin access denied")

    db = SessionLocal()

    existing = db.query(User).filter(User.username == username).first()
    if existing:
        db.close()
        raise HTTPException(status_code=400, detail="Username already exists")

    user = User(
        username=username,
        password=password,   # plain or mixed (per your decision)
        role=role,
        department=department,
        is_admin=True if role == "admin" else False,
    )

    db.add(user)
    db.commit()
    db.close()

    return RedirectResponse("/admin/users", status_code=303)
