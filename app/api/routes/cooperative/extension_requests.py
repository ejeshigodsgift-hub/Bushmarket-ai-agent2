from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db

from app.services.cooperative_extension_voting_service import (
    CooperativeExtensionVoteService
)

router = APIRouter(
    prefix="/cooperative/extensions",
    tags=["Cooperative Extensions"]
)

service = CooperativeExtensionVoteService()


@router.post("/vote")
async def cast_vote(
    payload: dict,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    user = request.state.user

    return await service.cast_vote(
        db=db,
        cooperative_id=payload["cooperative_id"],
        user_id=user["id"],
        membership_id=payload["membership_id"],
        round_number=payload["round_number"],
        vote=payload["vote"]
    )


@router.post("/evaluate")
async def evaluate_round(
    payload: dict,
    db: AsyncSession = Depends(get_db)
):
    return await service.evaluate_round(
        db=db,
        cooperative_id=payload["cooperative_id"],
        round_number=payload["round_number"]
    )