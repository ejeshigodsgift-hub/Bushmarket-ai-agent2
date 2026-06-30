import uuid
from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker,
)

from app.db.base import Base
from app.db.models.wallet import Wallet


# ==========================================
# TEST DATABASE
# ==========================================

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(
    TEST_DATABASE_URL,
    future=True
)

TestingSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)


# ==========================================
# DB SESSION FIXTURE
# ==========================================

@pytest.fixture
async def db_session():

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestingSessionLocal() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


# ==========================================
# WALLET FIXTURE
# ==========================================

@pytest.fixture
async def wallet(db_session):

    wallet = Wallet(
        id=str(uuid.uuid4()),
        user_id=str(uuid.uuid4()),
        balance=Decimal("0.00"),
        escrow_balance=Decimal("0.00"),
        ledger_balance=Decimal("0.00"),
        currency="NGN",
        version=1
    )

    db_session.add(wallet)

    await db_session.commit()
    await db_session.refresh(wallet)

    return wallet