from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker
)

from app.core.config import settings


engine = create_async_engine(
    settings.DATABASE_URL.replace(
        "postgresql+psycopg2",
        "postgresql+asyncpg"
    ),

    pool_pre_ping=True,
    pool_size=50,
    max_overflow=100,
    pool_recycle=1800
)

SessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)


async def get_db():

    async with SessionLocal() as db:
        yield db