from sqlalchemy.orm import Session

from app.db.models.market_product_price import MarketProductPrice


class MarketPricingService:

    # =========================
    # GET PRODUCT MARKET PRICES
    # =========================
    def get_market_prices(
        self,
        db: Session,
        product_id: str
    ):

        return db.query(MarketProductPrice).filter(
            MarketProductPrice.product_id == product_id,
            MarketProductPrice.is_available == True
        ).all()


market_pricing_service = MarketPricingService()