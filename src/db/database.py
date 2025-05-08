from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.config import DATABASE_URL

async_engine = create_async_engine(
    DATABASE_URL,
    echo=True,
    future=True,
    execution_options={"isolation_level": "AUTOCOMMIT"},
)
async_session_maker = async_sessionmaker(async_engine, expire_on_commit=False)


async def get_db_session() -> AsyncGenerator:
    try:
        session = async_session_maker()
        yield session
    finally:
        await session.close()
