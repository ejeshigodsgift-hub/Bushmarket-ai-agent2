import pytest
from fastapi import HTTPException
from decimal import Decimal
from app.services.wallet_service import WalletService

wallet_service = WalletService()


@pytest.mark.asyncio
async def test_create_wallet_success(db_session):
    wallet = await wallet_service.create_wallet(
        db=db_session,
        user_id="user123"
    )

    assert wallet.user_id == "user123"
    assert wallet.balance == Decimal("0.00")
    assert wallet.currency == "NGN"



@pytest.mark.asyncio
async def test_duplicate_wallet_rejected(
    db_session
):
    await wallet_service.create_wallet(
        db=db_session,
        user_id="user123"
    )

    with pytest.raises(HTTPException):
        await wallet_service.create_wallet(
            db=db_session,
            user_id="user123"
        )


@pytest.mark.asyncio
async def test_wallet_topup(
    db_session,
    wallet
):
    await wallet_service.topup_wallet(
        db=db_session,
        user_id=wallet.user_id,
        wallet_id=wallet.id,
        amount=Decimal("500"),
        reference="ref1",
        ledger_credit_account="credit",
        ledger_debit_account="debit"
    )

    assert wallet.balance ==  Decimal("500")




@pytest.mark.asyncio
async def test_wallet_topup_invalid_amount(
    db_session,
    wallet
):
    with pytest.raises(HTTPException):
        await wallet_service.topup_wallet(
            db=db_session,
            user_id=wallet.user_id,
            wallet_id=wallet.id,
            amount=Decimal("0"),
            reference="ref1",
            ledger_credit_account="credit",
            ledger_debit_account="debit"
        )


@pytest.mark.asyncio
async def test_wallet_withdrawal_success(
    db_session,
    wallet
):
    wallet.balance = Decimal("1000")

    await wallet_service.request_withdrawal(
        db=db_session,
        wallet_id=wallet.id,
        amount=Decimal("300"),
        reference="withdraw1"
    )

    assert wallet.balance == Decimal("700")


@pytest.mark.asyncio
async def test_wallet_withdrawal_insufficient_balance(
    db_session,
    wallet
):
    wallet.balance = Decimal("100")

    with pytest.raises(HTTPException):
        await wallet_service.request_withdrawal(
            db=db_session,
            wallet_id=wallet.id,
            amount=Decimal("500"),
            reference="withdraw1"
        )


