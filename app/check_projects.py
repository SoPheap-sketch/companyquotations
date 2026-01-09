from app.db import SessionLocal
from app.models import Project
db = SessionLocal()
projects = db.query(Project).all()
print ("ID | Client Name | Created At")
print ("-" * 40)
for p in projects:
    print (f"{p.id} | {p.client_name} | {p.created_at}")
db.close()