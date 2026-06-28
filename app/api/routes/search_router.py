from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db

from app.services.search_service import search_service

from app.schemas.search_schema import (
SearchRequest,
SearchResponse
)

router = APIRouter(
prefix="/search",
tags=["Search"]
)

@router.post(
"/",
response_model=SearchResponse
)
async def search_products(
    payload: SearchRequest,
    request: Request,
    db: AsyncSession = Depends(get_db)
):

    listings = await  search_service.search_products(
        db=db,
        query=payload.query,
        user_id=request.state.user["id"],
        limit=payload.limit
    )

    return {
        "query": payload.query,
        "total_results": len(listings),
        "results": listings
    }