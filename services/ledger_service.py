from sqlalchemy.orm import Session
from models.ledger import Ledger


class LedgerService:

    def get_user_history(self, db: Session, user_id: int):
        return db.query(Ledger).filter_by(user_id=user_id).all()

    def get_cooperative_history(self, db: Session, coop_id: int):
        return db.query(Ledger).filter_by(cooperative_id=coop_id).all()