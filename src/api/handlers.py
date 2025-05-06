from logging import getLogger
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.models import (
    UserCreate,
    UserDeletedResponse,
    UserGetByEmailRequest,
    UserGetByIdRequest,
    UserShowResponse,
    UserUpdatedResponse,
    UserUpdateRequest,
)
from src.db.dals import UserDAL
from src.db.database import get_db_session
from src.db.models import UserEntity
from src.utils import PasswordHasher

logger = getLogger(__name__)

user_router = APIRouter()


async def _create_new_user(body: UserCreate, session: AsyncSession) -> UserEntity:
    async with session.begin():
        user_dal = UserDAL(session)
        new_user = await user_dal.create_user(
            name=body.name,
            surname=body.surname,
            email=body.email,
            hashed_password=PasswordHasher.get_password_hash(body.password),
        )
        return new_user


async def _get_user(body: BaseModel, session: AsyncSession) -> UserEntity:
    async with session.begin():
        user_dal = UserDAL(session)
        filters = body.model_dump()
        user = await user_dal.get_user(filters)
        return user


async def _get_user_by_email(
    body: UserGetByEmailRequest, db: AsyncSession
) -> UserEntity:
    return await _get_user(body, db)


async def _get_user_by_id(user_id: UUID, db: AsyncSession) -> UserEntity:
    body = UserGetByIdRequest(user_id=user_id)
    body.user_id = str(user_id)
    return await _get_user(body, db)


async def _get_users(session: AsyncSession) -> List[UserEntity]:
    async with session.begin():
        user_dal = UserDAL(session)
        users = await user_dal.get_all_users()
        return users


async def _update_user(
    user_id: UUID, updated_user_params: dict, session: AsyncSession
) -> UUID | None:
    async with session.begin():
        user_dal = UserDAL(session)
        updated_user_id = await user_dal.update_user(
            user_id=user_id, values_dict=updated_user_params
        )
        return updated_user_id


async def _delete_user(user_id: UUID, session: AsyncSession) -> UUID | None:
    async with session.begin():
        user_dal = UserDAL(session)
        deleted_user_id = await user_dal.delete_user(user_id)
        return deleted_user_id


@user_router.post("/", response_model=UserShowResponse)
async def create_user(body: UserCreate, db: AsyncSession = Depends(get_db_session)):
    try:
        return await _create_new_user(body, db)
    except IntegrityError as err:
        logger.error(err)
        raise HTTPException(status_code=503, detail=f"Database error: {err}")


@user_router.get("/by-email")
async def get_user_by_email(
    body: UserGetByEmailRequest = Query(...),
    db_session: AsyncSession = Depends(get_db_session),
) -> UserShowResponse:
    return await _get_user_by_email(body, db_session)


@user_router.get("/")
async def get_user_by_id(
    user_id: UUID, db_session: AsyncSession = Depends(get_db_session)
) -> UserShowResponse:
    user = await _get_user_by_id(user_id, db_session)
    if user is None:
        raise HTTPException(
            status_code=404, detail=f"User with id {user_id} not found."
        )
    return user


@user_router.patch("/")
async def update_user_by_id(
    user_id: UUID,
    body: UserUpdateRequest,
    db_session: AsyncSession = Depends(get_db_session),
) -> UserUpdatedResponse:
    updated_user_params = body.model_dump(exclude_unset=True)

    if updated_user_params == {}:
        raise HTTPException(
            status_code=422,
            detail="At least one parameter for user update info should be provided",
        )

    user = await _get_user_by_id(user_id, db_session)
    if user is None:
        raise HTTPException(
            status_code=404, detail=f"User with id {user_id} not found."
        )
    try:
        updated_user_id = await _update_user(user_id, updated_user_params, db_session)
    except IntegrityError as err:
        logger.error(err)
        raise HTTPException(status_code=503, detail=f"Database error: {err}")
    return UserUpdatedResponse(updated_user_id=updated_user_id)


@user_router.delete("/")
async def delete_user_by_id(
    user_id: UUID, db_session: AsyncSession = Depends(get_db_session)
) -> UserDeletedResponse:
    user = await _get_user_by_id(user_id, db_session)

    if user is None:
        raise HTTPException(
            status_code=404, detail=f"User with id {user_id} not found."
        )

    deleted_user_id = await _delete_user(user_id, db_session)
    return UserDeletedResponse(deleted_user_id=deleted_user_id)
