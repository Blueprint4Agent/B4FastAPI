from contextlib import asynccontextmanager

from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.settings import SETTINGS


class Base(DeclarativeBase):
    pass


def _create_engine():
    db_url = SETTINGS.DATABASE_URL
    if db_url is None:
        raise RuntimeError("DATABASE_URL is not configured.")

    if db_url.startswith("sqlite+aiosqlite"):
        engine = create_async_engine(db_url, future=True)

        @event.listens_for(engine.sync_engine, "connect")
        def _set_sqlite_pragma(dbapi_connection, _connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

        return engine

    return create_async_engine(db_url, future=True, pool_pre_ping=True)


_ENGINE = None
_SESSION_FACTORY = None


def get_engine():
    global _ENGINE
    if _ENGINE is None:
        _ENGINE = _create_engine()
    return _ENGINE


def get_session_factory():
    global _SESSION_FACTORY
    if _SESSION_FACTORY is None:
        _SESSION_FACTORY = async_sessionmaker(
            get_engine(),
            autoflush=False,
            expire_on_commit=False,
        )
    return _SESSION_FACTORY


async def init_db() -> None:
    # Agent note: this template uses create_all for quick bootstrap.
    # Replace with Alembic migration workflow when schema history is needed.
    async with get_engine().begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def dispose_db() -> None:
    await get_engine().dispose()


@asynccontextmanager
async def get_db():
    session: AsyncSession = get_session_factory()()
    try:
        yield session
    finally:
        await session.close()
