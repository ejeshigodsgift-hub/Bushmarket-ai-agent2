from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.agent_permission_service import (
    agent_permission_service
)

from app.db.session import get_db
from app.services.agent_listing_service import AgentListingService

router = APIRouter(prefix="/agent/listings", tags=["Agent Listings"])

service = AgentListingService()


# =========================================
# CREATE DRAFT LISTING
# =========================================
@router.post("/create")
async def create_listing(
    payload: dict,
    request: Request,
    db: AsyncSession = Depends(get_db)
):

    if not request.state.user:
        raise HTTPException(401, "Unauthorized")

    agent_id = request.state.user["id"]

    await agent_permission_service.require_agent(
        db=db,
        user_id=agent_id
    )

    return await service.create_draft(
        db=db,
        agent_id=agent_id,
        payload=payload,
        ip=request.client.host
    )


# =========================================
# SUBMIT FOR REVIEW
# =========================================
@router.post("/submit/{listing_id}")
async def submit_listing(
    listing_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db)
):

    if not request.state.user:
        raise HTTPException(401, "Unauthorized")

    agent_id = request.state.user["id"]


    await agent_permission_service.require_agent(
        db=db,
        user_id=agent_id
    )

    return await service.submit_for_review(
        db=db,
        agent_id=agent_id,
        listing_id=listing_id
    )