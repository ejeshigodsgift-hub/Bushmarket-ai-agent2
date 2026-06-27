from decimal import Decimal

from app.db.models.ai_product_recommendation import (
AIProductRecommendation
)

class RecommendationLearningService:

async def process_click(
    self,
    recommendation: AIProductRecommendation
):
    # Track behavior
    recommendation.clicked = True
    recommendation.click_count += 1
    recommendation.cart_count += 1
    recommendation.purchase_count += 1

    # Increase confidence
    recommendation.confidence_score = min(
        Decimal("1.0000"),
        Decimal(str(recommendation.confidence_score))
        + Decimal("0.0500")
    )

async def process_add_to_cart(
    self,
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

async def process_purchase(
    self,
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

recommendation_learning_service = (
RecommendationLearningService()
)