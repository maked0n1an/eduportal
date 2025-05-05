from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from src.config import DATABASE_URL


async_engine = create_async_engine(DATABASE_URL, echo=True)
async_session_maker = async_sessionmaker(async_engine, expire_on_commit=False)


async def get_db_session() -> AsyncGenerator:
    try:
        session = async_session_maker()
        yield session
    finally:
        await session.close()
