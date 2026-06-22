from app.db.models.cooperative import Cooperative

WALLET_COOPERATIVE_ID = "system-wallet-coop"
MARKETPLACE_COOPERATIVE_ID = "system-marketplace-coop"
COOPERATIVE_COOPERATIVE_ID = "system-cooperative-coop"

async def seed_system_cooperatives(db):
    system_wallet_coop = Cooperative(
        id=WALLET_COOPERATIVE_ID,
        name="System Wallet Cooperative"
    )

    system_marketplace_coop = Cooperative(
        id=MARKETPLACE_COOPERATIVE_ID,
        name="System Marketplace Cooperative"
    )

    system_cooperative_coop = Cooperative(
        id=COOPERATIVE_COOPERATIVE_ID,
        name="System Cooperative Master"
    )

    db.add_all([
        system_wallet_coop,
        system_marketplace_coop,
        system_cooperative_coop
    ])

    await db.commit()