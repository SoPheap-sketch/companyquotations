
from app.auth.utils import verify_password

hashed = "$2b$12$3wshsm9hlmP176Gh/nMbsu90Mw1R2IKHvfGPd1nWzqdGX7chXJIoa"  # COPY ONE FROM DB
print(verify_password("123456", hashed))
