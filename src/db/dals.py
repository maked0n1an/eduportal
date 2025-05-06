from typing import List
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import UserEntity


class UserDAL:
    def __init__(self, db_session: AsyncSession):
        self.__db_session = db_session

    async def create_user(
        self, name: str, surname: str, email: str, hashed_password: str
    ) -> UserEntity:
        new_user = UserEntity(
            name=name, surname=surname, email=email, hashed_password=hashed_password
        )

        self.__db_session.add(new_user)
        await self.__db_session.flush()
        return new_user

    async def get_all_users(
        self,
        filters: dict | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> List[UserEntity]:
        query = select(UserEntity)

        if filters:
            query = query.filter_by(**filters)
        if limit:
            query = query.limit(limit)
        if offset:
            query = query.offset(offset)

        result = await self.__db_session.execute(query)
        return result.scalars().all()

    async def get_user(self, filters: dict) -> UserEntity | None:
        query = select(UserEntity).filter_by(**filters)
        result = await self.__db_session.execute(query)
        return result.scalar_one_or_none()

    async def update_user(self, user_id: UUID, values_dict: dict) -> UUID | None:
        query = (
            update(UserEntity)
            .where(UserEntity.user_id == user_id, UserEntity.is_active)
            .values(**values_dict)
            .returning(UserEntity.user_id)
        )
        res = await self.__db_session.execute(query)
        return res.scalar_one_or_none()

    async def update_many(self, filters: dict, values: dict) -> int:
        query = update(UserEntity).filter_by(**filters).values(**values)
        result = await self.__db_session.execute(query)
        await self.__db_session.flush()
        return result.rowcount

    async def delete_user(self, user_id: UUID) -> UUID | None:
        query = (
            update(UserEntity)
            .where(UserEntity.user_id == user_id, UserEntity.is_active)
            .values(is_active=False)
            .returning(UserEntity.user_id)
        )
        result = await self.__db_session.execute(query)
        return result.scalar_one_or_none()
