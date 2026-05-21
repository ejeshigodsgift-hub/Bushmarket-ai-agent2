from services.escrow_service import EscrowService


class CooperativeFinancialBridge:

    def __init__(self):
        self.escrow = EscrowService()

    # Called when user joins cooperative
    def process_contribution(self, db, user_id, coop_id, amount):

        return self.escrow.hold_funds(
            db=db,
            user_id=user_id,
            coop_id=coop_id,
            amount=amount
        )

    # Called when cooperative reaches funding success
    def trigger_bulk_payment(self, db, user_id, amount):

        return self.escrow.release_funds(
            db=db,
            user_id=user_id,
            amount=amount
        )

    # Called when cooperative fails
    def trigger_refund(self, db, user_id, coop_id, amount):

        return self.escrow.refund(
            db=db,
            user_id=user_id,
            coop_id=coop_id,
            amount=amount
        )