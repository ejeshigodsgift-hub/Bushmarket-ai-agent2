from sqlalchemy.orm import Session
from models.cooperative import Cooperative


class CooperativeRepository:

    def create(self, db: Session, coop: Cooperative):
        db.add(coop)
        db.commit()
        db.refresh(coop)
        return coop

    def get_by_product(self, db: Session, product_id: str, creator_id: int):
        return db.query(Cooperative).filter(
            Cooperative.product_id == product_id,
            Cooperative.creator_id == creator_id
        ).first()

    def get(self, db: Session, coop_id: int):
        return db.query(Cooperative).filter(Cooperative.id == coop_id).first()