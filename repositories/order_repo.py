from sqlalchemy.orm import Session
from models.order import CooperativeOrder


class OrderRepository:

    def create(self, db: Session, order: CooperativeOrder):
        db.add(order)
        db.commit()
        db.refresh(order)
        return order

    def get_by_coop(self, db: Session, coop_id: int):
        return db.query(CooperativeOrder).filter_by(
            cooperative_id=coop_id
        ).first()