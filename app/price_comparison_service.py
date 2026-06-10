from dataclasses import dataclass
from decimal import Decimal
from typing import List, Optional

from app.db.models.market_product_listing import MarketProductListing


@dataclass
class PriceComparisonResult:
    listing_id: str
    market_id: str
    market_name: str | None

    unit_price: Decimal
    market_fee: Decimal
    available_stock: int

    total_estimated_price: Decimal

    score: Decimal  # ranking score (AI decision)


class PriceComparisonService:

    # ======================================================
    # MAIN COMPARISON ENGINE
    # ======================================================
    def compare(
        self,
        listings: List[MarketProductListing],
        quantity: int = 1,
        priority: str = "cheapest"  # cheapest | stock | balanced
    ) -> List[PriceComparisonResult]:

        results: List[PriceComparisonResult] = []

        for listing in listings:

            if listing.available_stock < quantity:
                continue

            subtotal = listing.unit_price * quantity
            market_fee = listing.market_fee * quantity

            total = subtotal + market_fee

            score = self._score(
                listing=listing,
                total=total,
                priority=priority
            )

            results.append(
                PriceComparisonResult(
                    listing_id=listing.id,
                    market_id=listing.market_id,
                    market_name=getattr(listing.market, "market_name", None),
                    unit_price=listing.unit_price,
                    market_fee=listing.market_fee,
                    available_stock=listing.available_stock,
                    total_estimated_price=total,
                    score=score
                )
            )

        return sorted(results, key=lambda x: x.score, reverse=True)

    # ======================================================
    # SCORING ENGINE (AI DECISION LAYER)
    # ======================================================
    def _score(
        self,
        listing: MarketProductListing,
        total: Decimal,
        priority: str
    ) -> Decimal:

        stock_factor = Decimal(listing.available_stock)

        if priority == "cheapest":
            return Decimal("1") / (total + Decimal("0.01"))

        if priority == "stock":
            return stock_factor

        # balanced AI scoring
        return (
            (stock_factor * Decimal("0.4")) +
            ((Decimal("1") / (total + Decimal("0.01"))) * Decimal("0.6"))
        )


price_comparison_service = PriceComparisonService()