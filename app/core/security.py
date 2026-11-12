from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from app.core.config import settings
from pwdlib import PasswordHash

password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    return password_hash.verify(password, hashed_password)


def create_access_token(subject: str) -> str:
    expire = datetime.now(UTC) + timedelta(minutes=settings.access_token_expire_minutes)

    payload: dict[str, Any] = {
        "sub": subject,
        "exp": expire,
        "iat": datetime.now(UTC),
    }

    return jwt.encode(
        payload,
        settings.jwt_secret_key.get_secret_value(),
        algorithm=settings.jwt_algorithm,
    )


def decode_access_token(token: str) -> dict[str, Any]:
    return jwt.decode(
        token,
        settings.jwt_secret_key.get_secret_value(),
        algorithms=[settings.jwt_algorithm],
    )
