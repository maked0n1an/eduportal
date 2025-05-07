import uuid
from enum import Enum
from typing import List

from sqlalchemy import ARRAY, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class PortalRole(str, Enum):
    USER = "USER"
    ADMIN = "ADMIN"
    SUPERADMIN = "SUPERADMIN"


class BaseEntity(DeclarativeBase, AsyncAttrs):
    pass


class UserEntity(BaseEntity):
    __tablename__ = "users"

    user_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str]
    surname: Mapped[str]
    email: Mapped[str] = mapped_column(unique=True)
    is_active: Mapped[bool] = mapped_column(default=True)
    hashed_password: Mapped[str]
    roles: Mapped[List[PortalRole]] = mapped_column(
        ARRAY(String), default=[PortalRole.USER]
    )
