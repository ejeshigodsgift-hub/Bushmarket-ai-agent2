from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.db.models.cooperative_partial_procurement_proposal import (
    CooperativePartialProcurementProposal
)
from app.db.models.cooperative_partial_vote import CooperativePartialVote
from app.db.models.cooperative_membership import CooperativeMembership


class CooperativePartialVotingService:

    # =========================================
    # CREATE PROPOSAL
    # =========================================
    def create_proposal(
        self,
        db: Session,
        cooperative_id: str,
        listing_id: str,
        requested_quantity: int,
        available_quantity: int,
        total_cost: float,
        voting_window_hours: int = 48
    ):

        proposal = CooperativePartialProcurementProposal(
            id=f"pp_{datetime.utcnow().timestamp()}",
            cooperative_id=cooperative_id,
            listing_id=listing_id,
            requested_quantity=requested_quantity,
            available_quantity=available_quantity,
            total_cost=total_cost,
            status="voting",
            approval_threshold=100,
            expires_at=datetime.utcnow() + timedelta(hours=voting_window_hours)
        )

        db.add(proposal)
        db.commit()
        db.refresh(proposal)

        return proposal

    # =========================================
    # CAST VOTE
    # =========================================
    def cast_vote(
        self,
        db: Session,
        proposal_id: str,
        member_id: str,
        vote: bool
    ):

        proposal = db.get(CooperativePartialProcurementProposal, proposal_id)

        if not proposal or proposal.status != "voting":
            raise ValueError("Voting not active")

        if proposal.expires_at < datetime.utcnow():
            proposal.status = "expired"
            db.commit()
            raise ValueError("Voting expired")

        existing = db.execute(
            select(CooperativePartialVote).where(
                CooperativePartialVote.proposal_id == proposal_id,
                CooperativePartialVote.member_id == member_id
            )
        ).scalar_one_or_none()

        if existing:
            raise ValueError("Already voted")

        db.add(CooperativePartialVote(
            id=f"v_{datetime.utcnow().timestamp()}",
            proposal_id=proposal_id,
            member_id=member_id,
            vote=vote
        ))

        db.commit()

        return self.evaluate_votes(db, proposal)

    # =========================================
    # EVALUATION ENGINE (100% RULE)
    # =========================================
    def evaluate_votes(self, db: Session, proposal):

        votes = db.execute(
            select(CooperativePartialVote).where(
                CooperativePartialVote.proposal_id == proposal.id
            )
        ).scalars().all()

        members = db.execute(
            select(CooperativeMembership).where(
                CooperativeMembership.cooperative_id == proposal.cooperative_id,
                CooperativeMembership.status == "active"
            )
        ).scalars().all()

        total_members = len(members)
        approvals = sum(1 for v in votes if v.vote)

        approval_rate = (approvals / total_members) * 100 if total_members else 0

        if approval_rate >= 100:
            proposal.status = "approved"
            db.commit()
            return "APPROVED_100_PERCENT"

        if approval_rate < 50:
            proposal.status = "rejected"
            db.commit()
            return "REJECTED"

        return "VOTING_IN_PROGRESS"