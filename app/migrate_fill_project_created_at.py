# app/migrate_fill_project_created_at.py
from app.db import SessionLocal
from app.models import Project
from datetime import datetime

db = SessionLocal()

projects = db.query(Project).filter(Project.created_at == None).all()

for p in projects:
    p.created_at = datetime.utcnow()

db.commit()
db.close()

print("✅ Backfilled created_at for old projects")
