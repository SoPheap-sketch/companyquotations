from passlib.context import CryptContext

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, stored_password: str) -> bool:
    # Case 1: bcrypt hashed password
    if stored_password.startswith("$2b$"):
        return pwd_context.verify(plain_password, stored_password)

    # Case 2: plain-text password (legacy users)
    return plain_password == stored_password
