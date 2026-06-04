class EscrowDepositHandler:

async def handle(self, db, event):

    escrow_id = event.get(
        "escrow_account_id"
    )

    print(
        f"[ESCROW DEPOSIT] {escrow_id}"
    )