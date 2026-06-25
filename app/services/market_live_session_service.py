from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.market_live_session import (
    MarketLiveSession
)

from app.services.streaming_service import (
    streaming_service
)

from app.db.models.market_location import (
    MarketLocation
)

from app.services.audit_service import AuditService
from app.services.outbox_service import outbox_service


class MarketLiveSessionService:

    def __init__(self):
        self.audit = AuditService()

    # =========================================
    # CREATE LIVE SESSION
    # =========================================
    async def create_session(
        self,
        db: AsyncSession,
        market_id: str,
        agent_user_id: str,
        title: str,
        stream_channel: str,
        thumbnail_url: str | None = None
    ):

        market = await db.get(
            MarketLocation,
            market_id
        )

        if not market:
            raise HTTPException(
                404,
                "Market location not found"
            )

        existing = await db.execute(
            select(MarketLiveSession).where(
                MarketLiveSession.stream_channel
                == stream_channel
            )
        )

        if existing.scalar_one_or_none():
            raise HTTPException(
                400,
                "Stream channel already exists"
            )

        await   streaming_service.create_channel(
            stream_channel
        )

        session = MarketLiveSession(
            market_id=market_id,
            agent_user_id=agent_user_id,
            title=title,
            stream_channel=stream_channel,
            thumbnail_url=thumbnail_url,
            viewer_count=0,
            is_live=False,
            stream_status="scheduled"
        )

        db.add(session)

        await db.flush()
        await db.refresh(session)

        return session

    # =========================================
    # START SESSION
    # =========================================
    async def start_session(
        self,
        db: AsyncSession,
        session_id: str,
        user_id: str
    ):

        session = await db.get(
            MarketLiveSession,
            session_id
        )

        if not session:
            raise HTTPException(
                404,
                "Live session not found"
            )

        session.is_live = True
        session.stream_status = "live"
        session.started_at = datetime.now(
            timezone.utc
        )

        await streaming_service.start_broadcast(
            session.stream_channel
        )

        await self.audit.log(
            db=db,
            user_id=user_id,
            action="market_live_started",
            entity_type="market_live_session",
            entity_id=session.id,
            metadata={
                "market_id": session.market_id,
                "stream_channel": session.stream_channel
            }
        )

        await outbox_service.queue_event(
            db=db,
            topic="market.live.started",
            payload={
                "session_id": session.id,
                "market_id": session.market_id,
                "agent_user_id": session.agent_user_id,
                "stream_channel": session.stream_channel
            }
        )

        await db.flush()

        return session

    # =========================================
    # END SESSION
    # =========================================
    async def end_session(
        self,
        db: AsyncSession,
        session_id: str,
        user_id: str
    ):

        session = await db.get(
            MarketLiveSession,
            session_id
        )

        if not session:
            raise HTTPException(
                404,
                "Live session not found"
            )

        session.is_live = False
        session.stream_status = "ended"
        session.ended_at = datetime.now(
            timezone.utc
        )

        await streaming_service.end_broadcast(
            session.stream_channel
        )

        await self.audit.log(
            db=db,
            user_id=user_id,
            action="market_live_ended",
            entity_type="market_live_session",
            entity_id=session.id,
            metadata={
                "market_id": session.market_id,
                "viewer_count": session.viewer_count
            }
        )

        await outbox_service.queue_event(
            db=db,
            topic="market.live.ended",
            payload={
                "session_id": session.id,
                "market_id": session.market_id,
                "viewer_count": session.viewer_count
            }
        )

        await db.flush()

        return session

    # =========================================
    # INCREMENT VIEWERS
    # =========================================
    async def increment_viewers(
        self,
        db: AsyncSession,
        session_id: str
    ):

        session = await db.get(
            MarketLiveSession,
            session_id
        )

        if not session:
            raise HTTPException(
                404,
                "Live session not found"
            )

        session.viewer_count += 1

        await db.flush()

        return session

    # =========================================
    # DECREMENT VIEWERS
    # =========================================
    async def decrement_viewers(
        self,
        db: AsyncSession,
        session_id: str
    ):

        session = await db.get(
            MarketLiveSession,
            session_id
        )

        if not session:
            raise HTTPException(
                404,
                "Live session not found"
            )

        if session.viewer_count > 0:
            session.viewer_count -= 1

        await db.flush()

        return session

    # =========================================
    # GET ACTIVE SESSIONS
    # =========================================
    async def get_active_sessions(
        self,
        db: AsyncSession
    ):

        result = await db.execute(
            select(MarketLiveSession)
            .where(
                MarketLiveSession.is_live.is_(True)
            )
        )

        return result.scalars().all()

    # =========================================
    # GET MARKET SESSIONS
    # =========================================
    async def get_market_sessions(
        self,
        db: AsyncSession,
        market_id: str
    ):

        result = await db.execute(
            select(MarketLiveSession)
            .where(
                MarketLiveSession.market_id == market_id
            )
        )

        return result.scalars().all()


market_live_session_service = (
    MarketLiveSessionService()
)