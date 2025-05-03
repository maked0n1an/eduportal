from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from api.models import UserCreate, UserGetByEmail, UserShow
from db.dals import UserDAL
from db.database import get_db_session
from db.models import UserEntity


user_router = APIRouter()


async def _create_new_user(body: UserCreate, db: AsyncSession) -> UserEntity:
    async with db as session:
        user_dal = UserDAL(session)
        new_user = await user_dal.create_user(
            name=body.name,
            surname=body.surname,
            email=body.email
        )
        return new_user


async def _get_user(body: UserGetByEmail, db_session: AsyncSession) -> UserEntity:
    async with db_session as session:
        user_dal = UserDAL(session)
        filters = body.model_dump()
        return await user_dal.get_user(**filters)


@user_router.get("/")
async def get_user(
    body: UserGetByEmail = Query(),
    db_session: AsyncSession = Depends(get_db_session)
) -> UserShow:
    return await _get_user(body, db_session)


@user_router.post("/", response_model=UserShow)
async def create_user(
    body: UserCreate,
    db: AsyncSession = Depends(get_db_session)
):
    return await _create_new_user(body, db)
