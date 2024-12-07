from contextlib import asynccontextmanager

from sqlalchemy.engine import URL
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from typing import AsyncGenerator
from src.config.app_config import settings
from src.services.logger import LoggerProvider

log = LoggerProvider().get_logger(__name__)

database_url = URL.create(**settings.get_db_creds)
async_engine = create_async_engine(
    database_url,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
    pool_timeout=60.0,
)
async_session = async_sessionmaker(async_engine, expire_on_commit=False, class_=AsyncSession)


@asynccontextmanager
async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        try:
            yield session
        except Exception as e:
            log.warning('Session rollback because of exception: %s', e)
            await session.rollback()
            raise e
        finally:
            await session.close()


async def get_session():
    async with get_async_session() as session:
        yield session
