from sqlalchemy.orm import Session

from app.db.models.market_location import MarketLocation
from app.db.models.market_region import MarketRegion


class MarketService:

    # =========================
    # CREATE MARKET
    # =========================
    def create_market(
        self,
        db: Session,
        data: dict
    ):

        market = MarketLocation(**data)

        db.add(market)
        db.commit()
        db.refresh(market)

        return market

    # =========================
    # GET MARKETS
    # =========================
    def get_markets(
        self,
        db: Session
    ):

        return db.query(MarketLocation).filter(
            MarketLocation.is_active == True
        ).all()

    # =========================
    # GET SINGLE MARKET
    # =========================
    def get_market(
        self,
        db: Session,
        market_id: str
    ):

        return db.query(MarketLocation).filter(
            MarketLocation.id == market_id,
            MarketLocation.is_active == True
        ).first()


market_service = MarketService()