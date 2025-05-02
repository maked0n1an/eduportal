import uuid
import re

import uvicorn
from fastapi import APIRouter, FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict, EmailStr, field_validator
from sqlalchemy import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    AsyncAttrs,
    AsyncSession
)

from settings import DATABASE_URL


async_engine = create_async_engine(DATABASE_URL, echo=True)
async_session = async_sessionmaker(async_engine, expire_on_commit=False)


class BaseEntity(DeclarativeBase, AsyncAttrs):
    pass


class UserEntity(BaseEntity):
    __tablename__ = "users"

    user_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(nullable=False)
    surname: Mapped[str] = mapped_column(nullable=False)
    email: Mapped[str] = mapped_column(nullable=False, unique=True)
    is_active: Mapped[bool] = mapped_column(default=True)


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


LETTER_MATCH_PATTERN = re.compile(r"^[а-яА-Яa-zA-Z\-]+$")


class ConfigModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class UserShow(ConfigModel):
    user_id: uuid.UUID
    name: str
    surname: str
    email: EmailStr
    is_active: bool


class UserCreate(BaseModel):
    name: str
    surname: str
    email: EmailStr

    @field_validator("name")
    def validate_name(cls, value):
        if not LETTER_MATCH_PATTERN.match(value):
            raise HTTPException(
                status_code=422, detail="Name should contains only letters"
            )
        return value

    @field_validator("surname")
    def validate_surname(cls, value):
        if not LETTER_MATCH_PATTERN.match(value):
            raise HTTPException(
                status_code=422, detail="Surname should contains only letters"
            )
        return value


app = FastAPI(title="eduportal")

user_router = APIRouter()


async def _create_new_user(body: UserCreate) -> UserShow:
    async with async_session() as session:
        async with session.begin():
            user_dal = UserDAL(session)
            created_user = await user_dal.create_user(
                name=body.name,
                surname=body.surname,
                email=body.email
            )
            return UserShow(
                **body.model_dump(),
                user_id=created_user.user_id,
                is_active=created_user.is_active
            )


@user_router.post('/', response_model=UserShow)
async def create_user(body: UserCreate):
    return await _create_new_user(body)


main_api_router = APIRouter()

main_api_router.include_router(user_router, prefix="/user", tags=["user"])
app.include_router(main_api_router)


if __name__ == '__main__':
    uvicorn.run(app, host="0.0.0.0", port=8000)
