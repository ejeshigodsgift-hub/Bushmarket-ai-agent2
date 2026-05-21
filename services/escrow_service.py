from sqlalchemy.orm import Session
from models.wallet import Wallet
from models.ledger import Ledger


class EscrowService:

    # -------------------------
    # HOLD FUNDS (CONTRIBUTION)
    # -------------------------
    def hold_funds(self, db: Session, user_id: int, coop_id: int, amount: float):

        wallet = db.query(Wallet).filter_by(user_id=user_id).first()

        if wallet.balance < amount:
            raise Exception("Insufficient balance")

        wallet.balance -= amount
        wallet.locked_balance += amount

        ledger = Ledger(
            user_id=user_id,
            cooperative_id=coop_id,
            type="escrow_hold",
            amount=amount,
            status="success"
        )

        db.add(ledger)
        db.commit()

        return {"status": "held", "amount": amount}

    # -------------------------
    # RELEASE FUNDS (TO MARKETPLACE)
    # -------------------------
    def release_funds(self, db: Session, user_id: int, amount: float):

        wallet = db.query(Wallet).filter_by(user_id=user_id).first()

        if wallet.locked_balance < amount:
            raise Exception("Insufficient locked funds")

        wallet.locked_balance -= amount

        ledger = Ledger(
            user_id=user_id,
            type="payment",
            amount=amount,
            status="success"
        )

        db.add(ledger)
        db.commit()

        return {"status": "released"}

    # -------------------------
    # REFUND FUNDS
    # -------------------------
    def refund(self, db: Session, user_id: int, coop_id: int, amount: float):

        wallet = db.query(Wallet).filter_by(user_id=user_id).first()

        wallet.balance += amount

        ledger = Ledger(
            user_id=user_id,
            cooperative_id=coop_id,
            type="refund",
            amount=amount,
            status="success"
        )

        db.add(ledger)
        db.commit()

        return {"status": "refunded"}