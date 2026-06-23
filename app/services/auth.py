"""Auth helpers: bcrypt password hashing + JWT issue/verify."""
from __future__ import annotations

from datetime import datetime, timedelta

import bcrypt
from jose import JWTError, jwt

from app.config import get_settings

settings = get_settings()

# bcrypt only considers the first 72 bytes of a password; longer inputs raise on
# bcrypt >= 5. We truncate to match bcrypt's own limit (the same behaviour passlib
# used by default) so registration/login never error on long or multibyte inputs.
_BCRYPT_MAX_BYTES = 72


def hash_password(password: str) -> str:
    digest = bcrypt.hashpw(password.encode("utf-8")[:_BCRYPT_MAX_BYTES], bcrypt.gensalt())
    return digest.decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode("utf-8")[:_BCRYPT_MAX_BYTES], hashed.encode("utf-8"))
    except ValueError:
        return False


def create_access_token(subject: str) -> str:
    expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {"sub": subject, "exp": expire}
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> str | None:
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        return payload.get("sub")
    except JWTError:
        return None
