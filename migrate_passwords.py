from app.db import SessionLocal
from app.models import User
from app.auth.utils import hash_password

# bcrypt workaround
try:
    import bcrypt
    if not hasattr(bcrypt, "__about__"):
        bcrypt.__about__ = type("About", (), {"__version__": bcrypt.__version__})
except ImportError:
    pass


def is_bcrypt_hash(value: str) -> bool:
    return value.startswith("$2a$") or value.startswith("$2b$") or value.startswith("$2y$")


def migrate_passwords():
    db = SessionLocal()
    updated = 0
    skipped = 0

    try:
        users = db.query(User).all()

        for u in users:
            raw = (u.password or "").strip()

            if not raw:
                skipped += 1
                continue

            if is_bcrypt_hash(raw):
                continue

            print(f"🔧 Migrating password for user: {u.username}")
            u.password = hash_password(raw)
            updated += 1

        db.commit()
        print(f"✅ Migration complete | updated={updated}, skipped={skipped}")

    except Exception as e:
        db.rollback()
        print(f"❌ Migration failed: {e}")

    finally:
        db.close()


if __name__ == "__main__":
    migrate_passwords()
