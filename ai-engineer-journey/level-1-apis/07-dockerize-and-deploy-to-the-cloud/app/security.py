"""Password hashing + JWT tokens. Read this file slowly: this is how real logins work."""
import os
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

# NEVER hardcode a real secret. In production set SECRET_KEY as an environment variable.
SECRET_KEY = os.getenv("SECRET_KEY", "dev-only-change-me")
ALGORITHM = "HS256"
TOKEN_MINUTES = 30


def hash_password(plain: str) -> str:
    # bcrypt adds a random "salt" and is deliberately slow, so stolen hashes are hard to crack
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def create_token(username: str) -> str:
    # A JWT is a signed note: "this is sam, valid until 10:30". Anyone can READ it; nobody can FAKE it without SECRET_KEY.
    payload = {"sub": username, "exp": datetime.now(timezone.utc) + timedelta(minutes=TOKEN_MINUTES)}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def read_token(token: str) -> str | None:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])["sub"]
    except jwt.PyJWTError:          # expired, tampered with, or garbage
        return None
