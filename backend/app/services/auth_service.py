import random
import string
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from app.config import settings

VERIFICATION_CODE_LENGTH = 6
VERIFICATION_CODE_VALIDITY_MINUTES = 15

JWT_ALGORITHM = "HS256"
JWT_EXPIRY_HOURS = 24 * 7


def hash_password(plain_password: str) -> str:
    return bcrypt.hashpw(plain_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))


def generate_verification_code() -> str:
    return "".join(random.choices(string.digits, k=VERIFICATION_CODE_LENGTH))


def verification_code_expiry() -> datetime:
    return datetime.now(timezone.utc) + timedelta(minutes=VERIFICATION_CODE_VALIDITY_MINUTES)


def is_code_expired(expires_at: datetime | None) -> bool:
    if expires_at is None:
        return True
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    return datetime.now(timezone.utc) > expires_at


def create_access_token(patient_id: int, is_admin: bool = False) -> str:
    payload = {
        "sub": str(patient_id),
        "is_admin": is_admin,
        "exp": datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRY_HOURS),
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, settings.jwt_secret_key, algorithms=[JWT_ALGORITHM])
    except jwt.PyJWTError:
        return None