from app.db import SessionLocal
from app.models import AuditLog
from datetime import datetime

def write_audit_log(
        *,
        request,
        action: str,
        description: str,
        target_user_id: int | None = None
):
    db = SessionLocal()
    try:
        log = AuditLog(
            user_id=request.session.get("user_id"),
            username=request.session.get("username"),
            action=action,
            description=description,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            created_at=datetime.utcnow(),
        )
        db.add(log)
        db.commit()
    finally:
        db.close()