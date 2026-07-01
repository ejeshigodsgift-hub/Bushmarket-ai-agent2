from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.services.cooperative_partial_voting_service import (
    CooperativePartialVotingService
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
    return await service.evaluate_votes(
        db=db,
        proposal_id=proposal_id
    )