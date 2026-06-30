import uuid
from decimal import Decimal
from unittest.mock import AsyncMock

import pytest
import pytest_asyncio
from app.db.models.payment_intent import PaymentIntent

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
# =========================================


@pytest_asyncio.fixture
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

@pytest_asyncio.fixture
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



@pytest.fixture
def mock_idempotency_service():
    service = AsyncMock()
    service.is_processed.return_value = False
    service.mark_processed.return_value = None
    return service


@pytest.fixture
def mock_payment_service():
    service = AsyncMock()
    service.record_transaction.return_value = AsyncMock(
        id="tx1"
    )
    return service


@pytest.fixture
def mock_financial_core():
    service = AsyncMock()

    service.escrow_deposit.return_value = None
    service.credit_wallet.return_value = None

    return service


@pytest.fixture
def mock_audit_service():
    service = AsyncMock()
    service.log.return_value = None
    return service


@pytest.fixture
def mock_outbox_service():
    service = AsyncMock()
    service.queue_event.return_value = None
    return service


@pytest_asyncio.fixture
async def payment_intent(db_session):

    intent = PaymentIntent(
        id=str(uuid.uuid4()),
        user_id=str(uuid.uuid4()),
        reference="test-payment-ref",
        amount=Decimal("1000.00"),
        purpose="wallet_topup",
        status="pending"
    )

    db_session.add(intent)

    await db_session.commit()
    await db_session.refresh(intent)

    return intent