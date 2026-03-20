# app/services/auth.py
from fastapi import Request, HTTPException


# =========================
# Login required
# =========================
# def login_required(request: Request):
#     if not request.session.get("user_id"):
#         return RedirectResponse("/login", status_code=303)
def login_required(request: Request):
    if not request.session.get("user_id"):
        raise HTTPException(status_code=401)
# =========================
# Approver (Admin / Manager / CEO)
# =========================
def approver_required(request: Request):
    if not request.session.get("user_id"):
        raise HTTPException(status_code=401)

    role = request.session.get("role")
    if role not in ["admin", "manager", "ceo"]:
        raise HTTPException(
            status_code=403,
            detail="Approval permission required"
        )

# =========================
# Admin only
# =========================
def admin_only(request: Request):
    if not request.session.get("user_id"):
        raise HTTPException(status_code=401)

    if request.session.get("role") != "admin":
        raise HTTPException(status_code=403)
