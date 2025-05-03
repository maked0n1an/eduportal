import asyncio
from typing import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    AsyncSession,
    AsyncEngine
)

from config import TEST_DATABASE_URL
from db.models import BaseEntity
from db.database import get_db_session
from main import app


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session", name="engine")
async def engine_fixture():
    test_async_engine = create_async_engine(TEST_DATABASE_URL, future=True)

    async with test_async_engine.begin() as conn:
        await conn.run_sync(BaseEntity.metadata.drop_all)
        await conn.run_sync(BaseEntity.metadata.create_all)

    yield test_async_engine


@pytest.fixture(name="session")
async def session_fixture(engine: AsyncEngine):
    async_session_maker = async_sessionmaker(engine, expire_on_commit=False)
    async with async_session_maker() as session:
        yield session


@pytest.fixture(name="client")
async def client_fixture(session: AsyncSession):
    async def __override_db_session():
        yield session

    app.dependency_overrides[get_db_session] = __override_db_session

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as test_client:
        yield test_client

    app.dependency_overrides.clear()
