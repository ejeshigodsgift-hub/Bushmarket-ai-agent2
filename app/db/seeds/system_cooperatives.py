from app.db.models.cooperative import Cooperative



async def seed_system_cooperatives(db):
    system_wallet_coop = Cooperative(
        id="system-wallet-coop",
        name="System Wallet Cooperative"
    )
    

    system_marketplace_coop = Cooperative(
        id="system-marketplace-coop",
        name="System Marketplace Cooperative"
    )

    

    db.add_all([
        system_wallet_coop,
        system_marketplace_coop,
        
    ])

    await db.commit()