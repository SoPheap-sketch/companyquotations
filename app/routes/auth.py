# app/routes/auth.py

from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates

from app.db import SessionLocal
from app.models import User
from app.auth.utils import verify_password, validate_password_strength


router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

# =========================
# LOGIN PAGE
# =========================
@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse(
        "login.html",
        {
            "request": request,
            "mode": "change_password"
            if request.session.get("force_password_change")
            else "login",
        }
    )

# =========================
# LOGIN SUBMIT
# =========================
@router.post("/login")
def login_submit(
    request: Request,
    username: str = Form(...),
    password: str = Form(...)
):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == username).first()

        if not user:
            return templates.TemplateResponse(
                "login.html",
                {"request": request, "error": "Username not found", "mode": "login"},
                status_code=400
            )

        if not verify_password(password, user.password):
            return templates.TemplateResponse(
                "login.html",
                {"request": request, "error": "Incorrect password", "mode": "login"},
                status_code=400
            )

        if not user.is_active:
            return templates.TemplateResponse(
                "login.html",
                {
                    "request": request,
                    "error": "This account has been disabled. Contact admin.",
                    "mode": "login"
                },
                status_code=403
            )

        # session
        request.session["user_id"] = user.id
        request.session["username"] = user.username
        request.session["role"] = user.role

        # 🔒 FORCE PASSWORD CHANGE
        if user.force_password_change:
            request.session["force_password_change"] = True
            return templates.TemplateResponse(
                "login.html",
                {"request": request, "mode": "change_password"}
            )

        request.session["force_password_change"] = False
        return RedirectResponse("/", status_code=303)

    finally:
        db.close()

# =========================
# CHANGE PASSWORD SUBMIT
# =========================
@router.post("/change-password")
def change_password(
    request: Request,
    new_password: str = Form(...)
):
    # must be forced
    if not request.session.get("force_password_change"):
        return RedirectResponse("/", status_code=303)

    # ✅ validate password strength (USER ONLY)
    error = validate_password_strength(new_password)
    if error:
        return templates.TemplateResponse(
            "login.html",
            {
                "request": request,
                "mode": "change_password",  # 🔑 IMPORTANT
                "error": error,
            },
            status_code=400
        )

    db = SessionLocal()
    user = db.query(User).filter(
        User.id == request.session.get("user_id")
    ).first()

    if not user:
        db.close()
        raise HTTPException(status_code=404)

    # ✅ update password
    user.password = new_password
    user.force_password_change = False
    db.commit()
    db.close()

    # ✅ clear session flag
    request.session.pop("force_password_change", None)

    return RedirectResponse("/", status_code=303)

# =========================
# LOGOUT
# =========================
@router.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/login", status_code=303)
