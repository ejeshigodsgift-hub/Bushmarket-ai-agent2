# app/services/product_recommendation_service.py

from decimal import Decimal

from sqlalchemy import (
    select,
    func
)

import logging

logger = logging.getLogger(__name__)


from app.db.models.cooperative_demand_signal import (
    CooperativeDemandSignal
)

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.market_product_listing import (
    MarketProductListing
)

from app.db.models.listing_intelligence_score import (
    ListingIntelligenceScore
)

from app.db.models.product_recommendation_feature import (
    ProductRecommendationFeature
)

from app.db.models.ai_product_recommendation import (
    AIProductRecommendation
)


class ProductRecommendationService:

    async def recommend_products(
        self,
        db: AsyncSession,
        limit: int = 20
    ):

        stmt = (
            select(
                MarketProductListing,
                ListingIntelligenceScore
            )
            .join(
                ListingIntelligenceScore,
                ListingIntelligenceScore.listing_id
                == MarketProductListing.id
            )
            .where(
                MarketProductListing.is_active.is_(True)
            )
            .order_by(
                ListingIntelligenceScore.recommendation_score.desc()
            )
            .limit(limit)
        )

        result = await db.execute(stmt)

        rows = result.all()

        return [row[0] for row in rows]

    async def calculate_listing_score(
        self,
        db: AsyncSession,
        listing_id: str
    ):

        feature = await db.scalar(
            select(ProductRecommendationFeature)
            .where(
                ProductRecommendationFeature.listing_id
                == listing_id
            )
        )

        if not feature:
            return Decimal("0")

        score = (
            Decimal(str(feature.demand_score)) * Decimal("0.30")
            + Decimal(str(feature.purchase_score)) * Decimal("0.25")
            + Decimal(str(feature.cart_score)) * Decimal("0.15")
            + Decimal(str(feature.click_score)) * Decimal("0.10")
            + Decimal(str(feature.inventory_score)) * Decimal("0.10")
            + Decimal(str(feature.distance_score)) * Decimal("0.10")
        )

        return score



    async def rebuild_features(
        self,
        db: AsyncSession,
        listing_id: str
    ):

        try:

            recommendation_stats = await db.execute(
                select(
                    func.sum(
                    AIProductRecommendation.click_count
                    ),
                    func.sum(
                    AIProductRecommendation.cart_count
                    ),
                    func.sum(
                    AIProductRecommendation.purchase_count
                    )
                )
                .where(
                AIProductRecommendation.listing_id
                    == listing_id
                )
            )

            clicks, carts, purchases = (
                recommendation_stats.one()
            )

            clicks = clicks or 0
            carts = carts or 0
            purchases = purchases or 0

            demand_count = await db.scalar(
                select(
         func.count(CooperativeDemandSignal.id)
                ).where(
        CooperativeDemandSignal.product_id
                    == (
            select(MarketProductListing.product_id)
                        .where(
                        MarketProductListing.id == listing_id
                        )
                        .scalar_subquery()
                    )
                )
            )

            demand_count = demand_count or 0

            feature = await db.scalar(
            select(ProductRecommendationFeature)
                .where(
                ProductRecommendationFeature.listing_id
                    == listing_id
                )
            )

            if not feature:

                feature = ProductRecommendationFeature(
                    listing_id=listing_id
                )

                db.add(feature)

            feature.click_score = clicks
            feature.cart_score = carts
            feature.purchase_score = purchases
            feature.demand_score = demand_count

            feature.popularity_score = (
                clicks
                + carts * 2
                + purchases * 5
            )

            feature.final_score = (
                feature.popularity_score
                + demand_count
            )

            intelligence = await db.scalar(
            select(ListingIntelligenceScore)
                .where(
                ListingIntelligenceScore.listing_id
                    == listing_id
                )
            )

            if intelligence:

                intelligence.demand_score = (
                    feature.demand_score
                )

                intelligence.sales_score = (
                    feature.purchase_score
                )

                intelligence.recommendation_score = (
                    feature.final_score
                )

            await db.flush()

            return feature

        except Exception:

            logger.exception(
                f"Recommendation rebuild failed: {listing_id}"
            )

            await ai_observability_service.log_request(
                db=db,
                operation="recommendation_rebuild",
                status="failed",
                error_message=str(e),
                metadata={
                    "listing_id": listing_id
                }
            )

            raise


product_recommendation_service = (
    ProductRecommendationService()
)