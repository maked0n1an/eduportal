import asyncio
from datetime import timedelta
from typing import List

import asyncpg
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from main import app
from src.api.actions.auth import auth_settings
from src.config import TEST_DATABASE_URL
from src.db.models import PortalRole
from src.db.database import get_db_session
from src.db.models import BaseEntity
from src.security import create_access_token


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(name="engine", scope="session")
async def engine_fixture():
    test_async_engine = create_async_engine(TEST_DATABASE_URL, future=True)

    async with test_async_engine.begin() as conn:
        await conn.run_sync(BaseEntity.metadata.create_all)

    yield test_async_engine

    async with test_async_engine.begin() as conn:
        await conn.run_sync(BaseEntity.metadata.drop_all)


@pytest.fixture(name="session")
async def session_fixture(engine: AsyncEngine):
    async_session_maker = async_sessionmaker(engine, expire_on_commit=False)
    async with async_session_maker() as session:
        yield session
        await session.rollback()


@pytest.fixture(name="client", scope="function")
async def client_fixture(session: AsyncSession):
    async def __override_db_session():
        yield session

    app.dependency_overrides[get_db_session] = __override_db_session

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture(scope="session")
async def asyncpg_pool():
    pool = await asyncpg.create_pool("".join(TEST_DATABASE_URL.split("+asyncpg")))
    yield pool
    await pool.close()


@pytest.fixture(autouse=True)
async def clean_tables(asyncpg_pool):
    yield

    async with asyncpg_pool.acquire() as conn:
        await conn.execute("""TRUNCATE TABLE users RESTART IDENTITY CASCADE;""")


@pytest.fixture
async def get_user_from_database(asyncpg_pool):
    async def get_user_from_database_by_uuid(user_id: str):
        async with asyncpg_pool.acquire() as connection:
            return await connection.fetch(
                """SELECT * FROM users WHERE user_id = $1;""", user_id
            )

    return get_user_from_database_by_uuid


@pytest.fixture
async def create_user_in_database(asyncpg_pool):
    async def create_user_in_database(
        user_id: str,
        name: str,
        surname: str,
        email: str,
        is_active: bool,
        hashed_password: str,
        roles: List[PortalRole],
    ):
        async with asyncpg_pool.acquire() as connection:
            return await connection.execute(
                """INSERT INTO users VALUES ($1, $2, $3, $4, $5, $6, $7)""",
                user_id,
                name,
                surname,
                email,
                is_active,
                hashed_password,
                [role.value for role in roles],
            )

    return create_user_in_database


def create_test_auth_header_for_user(email: str) -> dict[str, str]:
    access_token = create_access_token(
        data={"sub": email},
        expires_delta=timedelta(minutes=auth_settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    return {"Authorization": f"Bearer {access_token}"}
