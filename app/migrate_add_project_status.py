from sqlalchemy import text
from app.db import engine

print("Starting migration: add projects.status")

with engine.connect() as conn:
    try:
        conn.execute(
            text("ALTER TABLE projects ADD COLUMN status VARCHAR(20) DEFAULT 'active'")
        )
        conn.commit()
        print("✅ Column 'status' added successfully")
    except Exception as e:
        print("⚠️ Migration skipped or failed:")
        print(e)
