from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import UserEntity


class UserDAL:
    def __init__(self, db_session: AsyncSession):
        self.__db_session = db_session

    async def create_user(
        self,
        name: str,
        surname: str,
        email: str
    ) -> UserEntity:
        new_user = UserEntity(
            name=name,
            surname=surname,
            email=email
        )

        self.__db_session.add(new_user)
        await self.__db_session.commit()
        return new_user


    async def get_user(
        self,
        **filter_by
    ) -> UserEntity:
        query = select(UserEntity).filter_by(**filter_by)
        result = await self.__db_session.execute(query)
        return result.scalar_one_or_none()