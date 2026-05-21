from sqlalchemy.orm import Session
from models.wallet import Wallet
from models.ledger import Ledger


class PaymentService:

    def deposit(self, db: Session, user_id: int, amount: float):

        wallet = db.query(Wallet).filter_by(user_id=user_id).first()

        if not wallet:
            wallet = Wallet(user_id=user_id, balance=0)
            db.add(wallet)

        wallet.balance += amount

        ledger = Ledger(
            user_id=user_id,
            type="payment",
            amount=amount,
            status="success"
        )

        db.add(ledger)
        db.commit()

        return {"status": "deposited", "amount": amount}