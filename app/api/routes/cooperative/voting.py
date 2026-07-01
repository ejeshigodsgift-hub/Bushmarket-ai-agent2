from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db

from app.services.cooperative_partial_voting_service import (
    CooperativePartialVotingService
)

from app.db.models.cooperative_partial_procurement_proposal import (
    CooperativePartialProcurementProposal
)

router = APIRouter(
    prefix="/cooperative/voting",
    tags=["Cooperative Voting"]
)

service = CooperativePartialVotingService()


@router.post("/proposal")
async def create_proposal(
    payload: dict,
    db: AsyncSession = Depends(get_db)
):
    return await service.create_proposal(
        db=db,
        cooperative_id=payload["cooperative_id"],
        listing_id=payload["listing_id"],
        requested_quantity=payload["requested_quantity"],
        available_quantity=payload["available_quantity"],
        total_cost=payload["total_cost"]
    )


@router.post("/vote")
async def cast_vote(
    payload: dict,
    db: AsyncSession = Depends(get_db)
):
    return await service.cast_vote(
        db=db,
        proposal_id=payload["proposal_id"],
        member_id=payload["member_id"],
        vote=payload["vote"]
    )


@router.post("/evaluate/{proposal_id}")
async def evaluate_votes(
    proposal_id: str,
    db: AsyncSession = Depends(get_db)
):

    result = await db.execute(
        select(
            CooperativePartialProcurementProposal
        ).where(
            CooperativePartialProcurementProposal.id
            == proposal_id
        )
    )

    proposal = result.scalar_one_or_none()

    if not proposal:
        return {
            "status": "proposal_not_found"
        }

    return await service.evaluate_votes(
        db=db,
        proposal=proposal
    )