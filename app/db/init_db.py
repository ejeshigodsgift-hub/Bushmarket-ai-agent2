from sqlalchemy.ext.asyncio import AsyncSession

from app.db.seeds.system_cooperatives import (
    seed_system_cooperatives
)

from app.db.seeds.seed_system_escrow_accounts import (
    seed_system_escrow_accounts
)

from app.db.seeds.seed_system_ledger_accounts import (
    seed_system_ledger_accounts
)


async def init_db(db: AsyncSession):

    await seed_system_cooperatives(db)
    await seed_system_ledger_accounts(db)
    await seed_system_escrow_accounts(db)
