import re
import uuid
from typing import Annotated

from fastapi import HTTPException
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


LETTER_MATCH_PATTERN = re.compile(r"^[а-яА-Яa-zA-Z\-]+$")


class ConfigModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


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


class UserShowResponse(ConfigModel):
    user_id: uuid.UUID
    name: str
    surname: str
    email: EmailStr
    is_active: bool


class UserUpdatedResponse(BaseModel):
    updated_user_id: uuid.UUID


class UserDeletedResponse(BaseModel):
    deleted_user_id: uuid.UUID


class UserGetByEmailRequest(BaseModel):
    email: EmailStr


class UserGetByIdRequest(BaseModel):
    user_id: uuid.UUID


class UserUpdateRequest(ConfigModel):
    surname: Annotated[str, Field(min_length=1)] | None = None
    name: Annotated[str, Field(min_length=1)] | None = None
    email: EmailStr | None = None

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
