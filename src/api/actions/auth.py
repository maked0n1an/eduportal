from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.models import UserGetByEmailRequest
from src.config import auth_settings
from src.db.dals import UserDAL
from src.db.database import get_db_session
from src.db.models import UserEntity
from src.utils import PasswordHasher

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login/token")


async def _get_user_by_email_for_auth(email: str, session: AsyncSession) -> UserEntity:
    async with session.begin():
        user_dal = UserDAL(session)
        filter = UserGetByEmailRequest(email=email)
        filter_dict = filter.model_dump()
        return await user_dal.get_user(filter_dict)


async def authenticate_user(
    email: str,
    password: str,
    db: AsyncSession,
) -> UserEntity | None:
    if not (user := await _get_user_by_email_for_auth(email, db)):
        return
    if not PasswordHasher.verify_password(password, user.hashed_password):
        return
    return user


async def get_current_user_from_token(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db_session),
) -> UserEntity:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
    )

    try:
        payload = jwt.decode(
            token,
            auth_settings.SECRET_KEY,
            algorithms=[auth_settings.ALGORITHM],
        )
        if not (email := payload.get("sub")):
            raise credentials_exception
        if not (user := await _get_user_by_email_for_auth(email, db)):
            raise credentials_exception
        return user
    except JWTError:
        raise credentials_exception
