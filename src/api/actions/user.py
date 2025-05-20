from typing import List
from uuid import UUID

from fastapi import HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.schemas import (
    UserCreate,
    UserGetByEmailRequest,
    UserGetByIdRequest,
)
from src.db.dals import UserDAL
from src.db.models import PortalRole, UserEntity
from src.utils import PasswordHasher


async def _create_new_user(
    body: UserCreate, session: AsyncSession
) -> UserEntity:
    async with session.begin():
        user_dal = UserDAL(session)
        new_user = await user_dal.create_user(
            name=body.name,
            surname=body.surname,
            email=body.email,
            hashed_password=PasswordHasher.get_password_hash(body.password),
            roles=[PortalRole.USER],
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


def check_user_permissions(
    target_user: UserEntity, current_user: UserEntity
) -> bool:
    if target_user.user_id == current_user.user_id:
        if PortalRole.SUPERADMIN in current_user.roles:
            raise HTTPException(
                status_code=406, detail="Superadmin cannot be deleted via API."
            )
        return True

    if not {PortalRole.ADMIN, PortalRole.SUPERADMIN}.intersection(
        current_user.roles
    ):
        return False

    if PortalRole.ADMIN in current_user.roles:
        if {PortalRole.SUPERADMIN, PortalRole.ADMIN}.intersection(
            target_user.roles
        ):
            return False

        if PortalRole.ADMIN in target_user.roles:
            return False

    return True
