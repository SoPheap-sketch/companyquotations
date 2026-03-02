# app/routes/admin.py

from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from app.db import SessionLocal
from app.models import User
from app.auth.utils import validate_password_strength
from app.models import User, AuditLog
from app.utils.audit import write_audit_log
from app.auth.utils import hash_password

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

    # 🔒 cannot edit yourself
    if user.id == request.session.get("user_id"):
        db.close()
        raise HTTPException(status_code=400, detail="You cannot edit your own role")

    # 🔒 prevent removing last admin
    if user.role == "admin" and role != "admin":
        admin_count = db.query(User).filter(User.role == "admin").count()
        if admin_count <= 1:
            db.close()
            raise HTTPException(
                status_code=400,
                detail="System must have at least one admin"
            )
    old_role = user.role
    old_department = user.department

    user.role = role
    user.department = department
    user.is_admin = True if role == "admin" else False

    db.commit()
    db.refresh(user)

 

    changes = []
    if old_role != role:
        changes.append(f"role: {old_role} → {role}")
    if old_department != department:
        changes.append(f"department: {old_department or '-'} → {department or '-'}")

    write_audit_log(
        request=request,
        action="UPDATE_USER",
        description=(
            f"Admin updated user '{user.username}' (ID {user.id}): "
            + ", ".join(changes)
        ),
        target_user_id=user.id,
    )

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
        username=username.strip(),
        password=hash_password(password.strip()),  
        role=role,
        department=department,
        is_admin=True if role == "admin" else False,
    )
    db.add(user)
    db.commit()
    db.close()
    return RedirectResponse("/admin/users", status_code=303)
# =========================
# ADMIN : DELETE USER
# =========================
@router.post("/users/delete")
def delete_user(
    request: Request,
    user_id: int = Form(...),
):
    # Admin only
    if request.session.get("role", "").lower() != "admin":
        raise HTTPException(status_code=403, detail="Admin access denied")
    db = SessionLocal()
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        db.close()
        raise HTTPException(status_code=404, detail="User not found")
    # Rule 1: cannot delete yourself
    if user.id == request.session.get("user_id"):
        db.close()
        raise HTTPException(status_code=400, detail="You cannot delete yourself")
    # Rule 2: cannot delete last admin
    if user.role.lower() == "admin":
        admin_count = db.query(User).filter(User.role.ilike("admin")).count()
        if admin_count <= 1:
            db.close()
            raise HTTPException(
                status_code=400,
                detail="System must have at least one admin"
            )
    db.delete(user)
    db.commit()
    db.close()

    request.session["flash"] = "User deleted successfully"
    return RedirectResponse("/admin/users", status_code=303)
# =========================
# ADMIN : RESET PASSWORD (DEBUG MODE)
# =========================
@router.post("/users/reset-password")
def reset_password(
    request: Request,
    user_id: int = Form(...),
    new_password: str = Form(...),
):
    if request.session.get("role", "").lower() != "admin":
        raise HTTPException(status_code=403)
    db = SessionLocal()
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        db.close()
        raise HTTPException(status_code=404)

    # update password
    user.password = hash_password(new_password.strip())
    user.force_password_change = True

    db.commit()
    db.refresh(user)
    db.close() 
    write_audit_log(
        request=request,
        action="RESET_PASSWORD",
        description=f"Admin reset password for user '{user.username}' (ID {user.id})",
        target_user_id=user.id,
    )

    request.session["flash_success"] = "Password reset successfully"
    return RedirectResponse("/admin/users", status_code=303)
@router.post("/users/toggle")
def toggle_user_status(
    request: Request,
    user_id: int = Form(...)
):
    if request.session.get("role", "").lower() != "admin":
        raise HTTPException(status_code=403)

    db = SessionLocal()
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        db.close()
        raise HTTPException(status_code=404)

    # 🔒 cannot disable yourself
    if user.id == request.session.get("user_id"):
        db.close()
        raise HTTPException(status_code=400, detail="You cannot disable yourself")

    # 🔒 cannot disable last active admin
    if user.role.lower() == "admin" and user.is_active:
        admin_count = db.query(User).filter(
            User.role.ilike("admin"),
            User.is_active == True
        ).count()
        if admin_count <= 1:
            db.close()
            raise HTTPException(
                status_code=400,
                detail="System must have at least one active admin"
            )

    #  TOGGLE STATUS
    user.is_active = not user.is_active
    db.commit()
    db.refresh(user)
    db.close()   

    action = "DISABLE_USER" if not user.is_active else "ENABLE_USER"

    write_audit_log(
        request=request,
        action=action,
        description=(
            f"Admin {'disabled' if action == 'DISABLE_USER' else 'enabled'} "
            f"user '{user.username}' (ID {user.id})"
        ),
        target_user_id=user.id,
    )

    return RedirectResponse("/admin/users", status_code=303)

@router.get("/audit-logs")
def audit_logs(request: Request):
    if request.session.get("role", "").lower() != "admin":
        raise HTTPException(status_code=403, detail="Admin access denied")

    db = SessionLocal()

    logs = (
        db.query(AuditLog)
        .order_by(AuditLog.created_at.desc())
        .limit(300)
        .all()
    )

    db.close()

    return templates.TemplateResponse(
        "admin_audit_logs.html",
        {
            "request": request,
            "logs": logs,
        }
    )