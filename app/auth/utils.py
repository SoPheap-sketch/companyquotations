# app/auth/utils.py

from passlib.context import CryptContext
import re

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, stored_password: str) -> bool:
    # Let passlib handle ALL bcrypt variants ($2a$, $2b$, $2y$)
    return pwd_context.verify(plain_password, stored_password)

def validate_password_strength(password: str) -> str | None:
    """
    Returns error message string if invalid,
    or None if password is strong enough.
    """
    if len(password) < 8:
        return "Password must be at least 8 characters long"

    if not re.search(r"[A-Z]", password):
        return "Password must contain at least one uppercase letter"

    if not re.search(r"[a-z]", password):
        return "Password must contain at least one lowercase letter"

    if not re.search(r"[0-9]", password):
        return "Password must contain at least one number"

    return None