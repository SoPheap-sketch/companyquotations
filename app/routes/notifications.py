# routes/notifications.py
from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse
from app.db import SessionLocal
from app.models import Notification


router = APIRouter()
@router.get("/notifications/{id}/read")
def mark_notification_read(id: int, request: Request):
    db = SessionLocal()
    try:
        n = db.query(Notification).filter(Notification.id == id).first()
        if not n:
            print(f"DEBUG: Notification {id} not found!") # Check terminal
            return RedirectResponse("/notifications", status_code=303)

        n.is_read = True
        db.commit()

        # Check terminal to see if these are actually None
        print(f"DEBUG: Notification {id} - Project: {n.project_id}, Work: {n.work_instruction_id}")

        if n.project_id:
            url = f"/projects/{n.project_id}"
            if n.work_instruction_id:
                url += f"#work-{n.work_instruction_id}"
            return RedirectResponse(url, status_code=303)

        print("DEBUG: No project_id found, falling back to /notifications")
        return RedirectResponse("/notifications", status_code=303)
    finally:
        db.close()