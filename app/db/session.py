from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker
)

from app.core.config import settings


DATABASE_URL = settings.DATABASE_URL.replace(
    "postgresql+psycopg2",
    "postgresql+asyncpg"
)

engine = create_async_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,        # FIXED (safe production baseline)
    max_overflow=20,     # FIXED
    pool_recycle=1800,
    echo=False
)

SessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False
)


async def get_db():

    async with SessionLocal() as db:
        yield db