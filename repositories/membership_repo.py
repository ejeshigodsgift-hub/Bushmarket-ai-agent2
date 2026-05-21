from sqlalchemy.orm import Session
from models.membership import Membership


class MembershipRepository:

    def add(self, db: Session, membership: Membership):
        db.add(membership)
        db.commit()
        db.refresh(membership)
        return membership

    def exists(self, db: Session, user_id: int, coop_id: int):
        return db.query(Membership).filter_by(
            user_id=user_id,
            cooperative_id=coop_id
        ).first()