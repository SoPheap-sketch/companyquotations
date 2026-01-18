from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from app.db import SessionLocal
from app.models import User

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")
# Admin : User list
@router.get("/users")
def admin_user(request: Request):
    if request.session.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access denied")
    db = SessionLocal()
    users = db.query(User).all()
    db.close()

    return templates.TemplateResponse(
        "admin_users.html",
        {
            "request": request,
            "users": users
        }
    )
# Admin: Update user 
@router.post("/users/update")
def update_user(
    request: Request,
    user_id:int = Form(...),
    role:str = Form(...),
    department:str = Form(...),
):
    # this is for the security admin only
    if request.session.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access denied")

    db = SessionLocal()
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        db.close()
        raise HTTPException(status_code=404, detail="User not found")
    # Update fields
    user.role =role
    user.department = department
    # keep is admin consistent
    user.is_admin = True if role == "admin" else False
    db.commit()
    db.close()
    return RedirectResponse("/admin/users", status_code=303)