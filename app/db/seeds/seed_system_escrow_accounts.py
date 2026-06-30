from sqlalchemy import select

from app.db.models.escrow_account import EscrowAccount

from app.db.seeds.system_cooperatives import (
    MARKETPLACE_COOPERATIVE_ID
)


async def seed_system_escrow_accounts(db):

    result = await db.execute(
        select(EscrowAccount).where(
            EscrowAccount.cooperative_id
            == MARKETPLACE_COOPERATIVE_ID
        )
    )

    existing = result.scalar_one_or_none()

    if existing:
        return

    db.add(
        EscrowAccount(
            cooperative_id=MARKETPLACE_COOPERATIVE_ID,
            status="active"
        )
    )

    await db.commit()