from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from models.cooperative import Cooperative, CoopStatus
from models.membership import Membership, MembershipStatus
from repositories.cooperative_repo import CooperativeRepository
from repositories.membership_repo import MembershipRepository


class CooperativeService:

    def __init__(self):
        self.coop_repo = CooperativeRepository()
        self.member_repo = MembershipRepository()

    # -----------------------------
    # CREATE COOPERATIVE
    # -----------------------------
    def create_cooperative(self, db: Session, user_id: int, data):

        # Anti-duplicate rule (same product + creator)
        existing = self.coop_repo.get_by_product(db, data.product_id, user_id)
        if existing:
            raise Exception("Duplicate cooperative for this product is not allowed")

        coop = Cooperative(
            creator_id=user_id,
            product_id=data.product_id,
            category=data.category,
            quantity_target=data.quantity_target,
            member_target=data.member_target,
            contribution_amount=data.contribution_amount,
            funding_target=data.member_target * data.contribution_amount,
            status=CoopStatus.active,
        )

        return self.coop_repo.create(db, coop)

    # -----------------------------
    # JOIN COOPERATIVE
    # -----------------------------
    def join_cooperative(self, db: Session, user_id: int, coop: Cooperative):

        # prevent duplicate membership
        if self.member_repo.exists(db, user_id, coop.id):
            raise Exception("Already joined this cooperative")

        membership = Membership(
            user_id=user_id,
            cooperative_id=coop.id,
            contribution_amount=coop.contribution_amount,
            status=MembershipStatus.pending
        )

        return self.member_repo.add(db, membership)

    # -----------------------------
    # LIFECYCLE UPDATE
    # -----------------------------
    def evaluate_lifecycle(self, db: Session, coop: Cooperative):

        # funding check
        members = db.query(Membership).filter(
            Membership.cooperative_id == coop.id,
            Membership.status == MembershipStatus.active
        ).count()

        if members >= coop.member_target:
            coop.status = CoopStatus.funded

        # expiry rule (60 days max)
        age_limit = coop.created_at + timedelta(days=coop.lifespan_days)
        if datetime.utcnow() > age_limit:
            coop.status = CoopStatus.expired

        db.commit()
        return coop