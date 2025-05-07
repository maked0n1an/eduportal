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

    @property
    def is_superadmin(self) -> bool:
        return PortalRole.SUPERADMIN in self.roles

    @property
    def is_admin(self) -> bool:
        return PortalRole.ADMIN in self.roles

    def enrich_admin_roles_by_admin_role(self):
        if not self.is_admin:
            return {*self.roles, PortalRole.ADMIN}

    def remove_admin_privileges_from_model(self):
        if self.is_admin:
            return {role for role in self.roles if role != PortalRole.ADMIN}
