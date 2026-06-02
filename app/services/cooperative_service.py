from datetime import datetime

from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.db.models.cooperative import Cooperative
from app.db.models.cooperative_membership import CooperativeMembership

from app.services.audit_service import AuditService
from app.services.outbox_service import outbox_service
from app.integrations.redis_client import redis_client


class CooperativeService:

    def __init__(self):
        self.audit = AuditService()

    # ====================================================
    # CREATE COOPERATIVE
    # ====================================================
    def create_cooperative(
        self,
        db: Session,
        creator,
        data: dict,
        ip: str
    ):

        # =========================
        # VALIDATION RULES (SOFT-CODED LATER)
        # =========================

        if len(data["product_ids"]) > 3:
            raise HTTPException(400, "Max 3 products allowed")

        if data["max_members"] > 30:
            raise HTTPException(400, "Max 30 members allowed")

        if data["life_span_days"] > 60:
            raise HTTPException(400, "Max lifespan exceeded")

        # =========================
        # CREATE COOPERATIVE
        # =========================
        coop = Cooperative(
            creator_id=creator.id,
            title=data["title"],
            product_ids=data["product_ids"],
            target_quantity=data["target_quantity"],
            target_amount=data["target_amount"],
            contribution_per_member=data["contribution_per_member"],
            max_members=data["max_members"],
            life_span_days=data["life_span_days"],
            status="draft",
            discount_flag=data.get("discount_flag", False)
        )

        db.add(coop)
        db.flush()

        # =========================
        # AUDIT
        # =========================
        self.audit.log(
            db=db,
            user_id=creator.id,
            action="cooperative_created",
            entity_type="cooperative",
            entity_id=coop.id,
            metadata={"coop_id": str(coop.id)},
            ip=ip
        )

        # =========================
        # OUTBOX EVENT
        # =========================
        outbox_service.queue_event(
            db=db,
            topic="cooperative.created",
            payload={
                "cooperative_id": str(coop.id),
                "creator_id": str(creator.id)
            }
        )

        db.commit()
        db.refresh(coop)

        return coop

    # ====================================================
    # GET COOPERATIVE
    # ====================================================
    def get_cooperative(self, db: Session, coop_id: str):

        coop = db.query(Cooperative).filter(
            Cooperative.id == coop_id
        ).first()

        if not coop:
            raise HTTPException(404, "Cooperative not found")

        return coop

    # ====================================================
    # JOIN COOPERATIVE
    # ====================================================
    def join_cooperative(
        self,
        db: Session,
        user,
        coop_id: str,
        ip: str
    ):

        coop = self.get_cooperative(db, coop_id)

        # =========================
        # CHECK DUPLICATE MEMBERSHIP
        # =========================
        existing = db.query(CooperativeMembership).filter(
            CooperativeMembership.cooperative_id == coop_id,
            CooperativeMembership.user_id == user.id
        ).first()

        if existing:
            raise HTTPException(400, "Already joined this cooperative")

        # =========================
        # CHECK CAPACITY
        # =========================
        member_count = db.query(CooperativeMembership).filter(
            CooperativeMembership.cooperative_id == coop_id
        ).count()

        if member_count >= coop.max_members:
            raise HTTPException(400, "Cooperative full")

        membership = CooperativeMembership(
            cooperative_id=coop_id,
            user_id=user.id,
            status="pending",
            joined_at=datetime.utcnow()
        )

        db.add(membership)
        db.flush()

        # =========================
        # REDIS EVENT
        # =========================
        redis_client.publish("cooperative.events", {
            "event": "member_joined",
            "cooperative_id": coop_id,
            "user_id": user.id
        })

        # =========================
        # OUTBOX
        # =========================
        outbox_service.queue_event(
            db=db,
            topic="cooperative.member_joined",
            payload={
                "cooperative_id": coop_id,
                "user_id": user.id
            }
        )

        self.audit.log(
            db=db,
            user_id=user.id,
            action="cooperative_joined",
            entity_type="cooperative",
            entity_id=coop_id,
            metadata={},
            ip=ip
        )

        db.commit()
        db.refresh(membership)

        return membership

    # ====================================================
    # GET ACTIVE COOPERATIVES
    # ====================================================
    def get_active_cooperatives(self, db: Session):

        return db.query(Cooperative).filter(
            Cooperative.status.in_(["active", "funding"])
        ).all()


cooperative_service = CooperativeService()