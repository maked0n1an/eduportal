from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.models import (
    Token,
    TokenTypeEnum,
    UserGetByEmailRequest,
    UserShowResponse,
)
from src.config import auth_settings
from src.db.dals import UserDAL
from src.db.database import get_db_session
from src.db.models import UserEntity
from src.security import create_access_token
from src.utils import PasswordHasher

login_router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login/token")


async def _get_user_by_email_for_auth(email: str, db: AsyncSession) -> UserEntity:
    async with db as session:
        async with session.begin():
            user_dal = UserDAL(session)
            filter = UserGetByEmailRequest(email=email)
            filter_dict = filter.model_dump()
            return await user_dal.get_user(filter_dict)


async def _authenticate_user(
    email: str,
    password: str,
    db: AsyncSession,
) -> UserEntity | None:
    if not (user := await _get_user_by_email_for_auth(email, db)):
        return
    is_password_verified = PasswordHasher.verify_password(
        password, user.hashed_password
    )
    if is_password_verified:
        return user


async def _get_current_user_from_token(
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


@login_router.get("/test_auth_endpoint")
async def sample_endpoint_under_jwt(
    current_user: UserShowResponse = Depends(_get_current_user_from_token),
):
    return {"success": True, "current_user": current_user}


@login_router.post("/token")
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db_session),
) -> Token:
    if not (
        user := await _authenticate_user(form_data.username, form_data.password, db)
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    access_token_expires = timedelta(minutes=auth_settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email, "other_custom_data": [1, 2, 3, 4]},
        expires_delta=access_token_expires,
    )
    return Token(access_token=access_token, token_type=TokenTypeEnum.BEARER)
