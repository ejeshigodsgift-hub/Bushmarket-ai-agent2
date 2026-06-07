from pydantic import BaseModel
from typing import List, Optional


class SearchRequest(BaseModel):
    query: str
    user_id: Optional[str] = None
    limit: int = 20


class SearchResultItem(BaseModel):
    listing_id: str
    product_name: str
    image_url: Optional[str]
    unit_price: float
    market_name: str
    availability: int


class SearchResponse(BaseModel):
    query: str
    total_results: int
    results: List[SearchResultItem]