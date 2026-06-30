from sqlalchemy import select

from app.db.models.ledger_account import LedgerAccount

from app.db.seeds.system_cooperatives import (
    MARKETPLACE_COOPERATIVE_ID,
)


async def seed_system_ledger_accounts(db):

    # =====================================
    # MARKETPLACE ESCROW LEDGER
    # =====================================

    result = await db.execute(
        select(LedgerAccount).where(
            LedgerAccount.account_type == "escrow",
            LedgerAccount.cooperative_id == MARKETPLACE_COOPERATIVE_ID
        )
    )

    existing = result.scalar_one_or_none()

    if not existing:

        db.add(
            LedgerAccount(
                cooperative_id=MARKETPLACE_COOPERATIVE_ID,
                account_type="escrow",
                currency="NGN",
                is_active=True
            )
        )

    await db.commit()