# app/services/notifications.py
from app.db import SessionLocal
from app.models import Notification

def get_unread_notification_count(request):
    user_id = request.session.get("user_id")
    if not user_id:
        return 0

    db = SessionLocal()
    try:
        return (
            db.query(Notification)
            .filter(
                Notification.user_id == user_id,
                Notification.is_read == False
            )
            .count()
        )
    finally:
        db.close()
