# =========================================
# FILE: app/services/market_service.py
# =========================================

from typing import Sequence

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.market_location import MarketLocation


class MarketService:

    # =========================================
    # GET MARKETS
    # =========================================
    async def get_markets(
        self,
        db: AsyncSession
    ) -> Sequence[MarketLocation]:

        stmt = (
            select(MarketLocation)
            .where(MarketLocation.is_active.is_(True))
            .order_by(MarketLocation.name.asc())
        )

        result = await db.execute(stmt)

        return result.scalars().all()

    # =========================================
    # GET MARKET
    # =========================================
    async def get_market_by_id(
        self,
        db: AsyncSession,
        market_id: str
    ) -> MarketLocation:

        stmt = (
            select(MarketLocation)
            .where(
                MarketLocation.id == market_id,
                MarketLocation.is_active.is_(True)
            )
            .limit(1)
        )

        result = await db.execute(stmt)

        market = result.scalar_one_or_none()

        if not market:
            raise HTTPException(
                status_code=404,
                detail="Market not found"
            )

        return market

    # =========================================
    # CREATE MARKET
    # =========================================
    async def create_market(
        self,
        db: AsyncSession,
        payload: dict
    ) -> MarketLocation:

        market = MarketLocation(
            name=payload["name"].strip(),
            code=payload["code"].upper().strip(),
            region_id=payload["region_id"],
            address=payload.get("address"),
            city=payload.get("city"),
            state=payload.get("state"),
            latitude=payload.get("latitude"),
            longitude=payload.get("longitude"),
            is_active=True
        )

        try:

            db.add(market)

            await db.commit()

            await db.refresh(market)

            return market

        except IntegrityError:

            await db.rollback()

            raise HTTPException(
                status_code=409,
                detail="Market already exists"
            )


market_service = MarketService()