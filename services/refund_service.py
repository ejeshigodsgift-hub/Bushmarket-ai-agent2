from sqlalchemy.orm import Session
from models.wallet import Wallet
from models.ledger import Ledger


class RefundService:

    def refund_user(self, db: Session, user_id: int, coop_id: int, amount: float):

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

        return {"status": "refund_success"}