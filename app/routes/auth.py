# app/rutes/auth.py


from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates

from app.db import SessionLocal
from app.models import User
from app.auth.utils import verify_password   

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

# =========================
# LOGIN PAGE
# =========================
@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse(
        "login.html",
        {"request": request}
    )


# =========================
# LOGIN SUBMIT (FIXED)
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
       
        if not user or not verify_password(password, user.password):
            return templates.TemplateResponse(
                "login.html",
                {
                    "request": request,
                    "error": "Invalid username or password"
                },
                status_code=400
            )

        request.session["user_id"] = user.id
        request.session["username"] = user.username
        request.session["is_admin"] = user.is_admin
        
        request.session["role"] = user.role
        request.session["department"] = user.department
        request.session["job_title"] = user.job_title
        return RedirectResponse("/", status_code=303)

    finally:
        db.close()


# =========================
# LOGOUT
# =========================
@router.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/login", status_code=303)
