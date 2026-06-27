from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.ai_product_recommendation import (
    AIProductRecommendation
)

from app.services.product_recommendation_service import (
    product_recommendation_service
)


class RecommendationLearningService:

    async def process_click(
        self,
        db: AsyncSession,
        recommendation: AIProductRecommendation
    ):
        # Track behavior
        recommendation.clicked = True
        recommendation.click_count += 1

        # Increase confidence
        recommendation.confidence_score = min(
            Decimal("1.0000"),
            Decimal(str(recommendation.confidence_score))
            + Decimal("0.0500")
        )

        await product_recommendation_service.rebuild_features(
            db,
            recommendation.listing_id
        )

    async def process_add_to_cart(
        self,
        db: AsyncSession,
        recommendation: AIProductRecommendation
    ):
        # Track behavior
        recommendation.added_to_cart = True
        recommendation.cart_count += 1

        # Increase confidence
        recommendation.confidence_score = min(
            Decimal("1.0000"),
            Decimal(str(recommendation.confidence_score))
            + Decimal("0.1000")
        )

        await product_recommendation_service.rebuild_features(
            db,
            recommendation.listing_id
        )

    async def process_purchase(
        self,
        db: AsyncSession,
        recommendation: AIProductRecommendation
    ):
        # Track behavior
        recommendation.purchased = True
        recommendation.purchase_count += 1

        # Increase confidence
        recommendation.confidence_score = min(
            Decimal("1.0000"),
            Decimal(str(recommendation.confidence_score))
            + Decimal("0.2000")
        )

        await product_recommendation_service.rebuild_features(
            db,
            recommendation.listing_id
        )


recommendation_learning_service = (
    RecommendationLearningService()
)