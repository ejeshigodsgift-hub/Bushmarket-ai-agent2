
import pytest

@pytest.mark.asyncio
async def test_escrow_balance_consistency(
    escrow_account
):
    assert (
        escrow_account.total_deposited
        >=
        escrow_account.available_balance
    )

@pytest.mark.asyncio
async def test_escrow_not_negative(
    escrow_account
):
    assert escrow_account.available_balance >= 0



