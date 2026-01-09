from datetime import datetime
from app.db import SessionLocal
from app.models import Project

db = SessionLocal()

projects = db.query(Project).filter(Project.created_at == None).all()

for p in projects:
    p.created_at = datetime.utcnow()

db.commit()
db.close()

print("✅ Project created_at backfilled")
