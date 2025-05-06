from datetime import datetime, timedelta, timezone

from jose import jwt

from src.config import auth_settings


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc)

    if expires_delta:
        expire += expires_delta
    else:
        expire += timedelta(minutes=auth_settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, auth_settings.SECRET_KEY, algorithm=auth_settings.ALGORITHM
    )
    return encoded_jwt
