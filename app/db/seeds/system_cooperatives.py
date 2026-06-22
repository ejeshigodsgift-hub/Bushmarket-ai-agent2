from sqlalchemy import select

from app.db.models.cooperative import Cooperative


async def seed_system_cooperatives(db):

    for coop_id, name in [
        ("system-wallet-coop", "System Wallet Cooperative"),
        ("system-marketplace-coop", "System Marketplace Cooperative"),
    ]:

        existing = await db.execute(
            select(Cooperative).where(
                Cooperative.id == coop_id
            )
        )

        if existing.scalar_one_or_none():
            continue

        db.add(
            Cooperative(
                id=coop_id,
                name=name
            )
        )

    await db.commit()