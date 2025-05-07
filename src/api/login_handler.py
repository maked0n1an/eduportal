from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.actions.auth import authenticate_user
from src.api.schemas import Token, TokenTypeEnum
from src.config import auth_settings
from src.db.database import get_db_session
from src.security import create_access_token

login_router = APIRouter()


@login_router.post("/token")
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db_session),
) -> Token:
    if not (
        user := await authenticate_user(form_data.username, form_data.password, db)
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
