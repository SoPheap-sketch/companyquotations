from sqlalchemy import text
from app.db import engine

print("🔧 Migrating projects table...")

with engine.connect() as conn:
    try:
        conn.execute(
            text("ALTER TABLE projects ADD COLUMN status VARCHAR(20) DEFAULT 'active'")
        )
        print("✅ status added")
    except Exception as e:
        print("ℹ️ status already exists")

    try:
        conn.execute(
            text("ALTER TABLE projects ADD COLUMN created_at DATETIME")
        )
        print("✅ created_at added")
    except Exception as e:
        print("ℹ️ created_at already exists")

    try:
        conn.execute(
            text("ALTER TABLE projects ADD COLUMN updated_at DATETIME")
        )
        print("✅ updated_at added")
    except Exception as e:
        print("ℹ️ updated_at already exists")

    conn.commit()

print("🎉 Migration complete")
