from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.services.search_service import search_service
from app.schemas.search_schema import SearchRequest, SearchResponse

router = APIRouter(prefix="/search", tags=["Search"])


@router.post("/")
async def search(
    payload: SearchRequest,
    db: AsyncSession = Depends(get_db)
):

    listings = await search_service.search_products(
        db=db,
        query=payload.query,
        limit=payload.limit
    )

    return {
        "query": payload.query,
        "total_results": len(listings),
        "results": [
            {
                "listing_id": l.id,
                "product_name": l.product.name,
                "image_url": l.product.image_url,
                "unit_price": float(l.unit_price),
                "market_name": l.market.market_name,
                "availability": l.available_stock
            }
            for l in listings
        ]
    }