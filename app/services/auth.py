from fastapi import Request, HTTPException
from fastapi.responses import RedirectResponse

# =========================
# Login required (ALL USERS)
# =========================
def login_required(request: Request):
    if not request.session.get("user_id"):
        raise HTTPException(
            status_code=303,
            headers={"Location": "/login"}
        )
# =========================
# Admin required
# =========================
def admin_required(request: Request):
    if not request.session.get("user_id"):
        raise HTTPException(
            status_code=303,
            headers={"Location": "/login"}
        )

    if not request.session.get("is_admin"):
        raise HTTPException(
            status_code=303,
            headers={"Location": "/"}
        )
