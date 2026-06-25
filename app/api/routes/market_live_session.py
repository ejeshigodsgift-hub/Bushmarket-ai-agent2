# =========================================
# FILE: app/api/routes/market_live_sessions.py
# =========================================

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request
)

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db

from app.db.models.market_live_session import (
    MarketLiveSession
)

from app.services.streaming_service import (
    streaming_service
)

from app.services.market_live_session_service import (
    market_live_session_service
)

from app.services.agent_permission_service import (
    agent_permission_service
)

router = APIRouter(
    prefix="/market-live",
    tags=["Market Live Sessions"]
)


# =========================================
# CREATE SESSION
# =========================================
@router.post("/create")
async def create_session(
    payload: dict,
    request: Request,
    db: AsyncSession = Depends(get_db)
):

    if not request.state.user:
        raise HTTPException(401, "Unauthorized")

    await agent_permission_service.require_agent(
        db,
        request.state.user["id"]
    )

    session = await market_live_session_service.create_session(
        db=db,
        market_id=payload["market_id"],
        agent_user_id=request.state.user["id"],
        title=payload["title"],
        stream_channel=payload["stream_channel"],
        thumbnail_url=payload.get("thumbnail_url")
    )

    await db.commit()

    return session


# =========================================
# START SESSION
# =========================================
@router.post("/start/{session_id}")
async def start_session(
    session_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db)
):

    if not request.state.user:
        raise HTTPException(401, "Unauthorized")

    await agent_permission_service.require_agent(
        db,
        request.state.user["id"]
    )

    session = await market_live_session_service.start_session(
        db=db,
        session_id=session_id,
        user_id=request.state.user["id"]
    )

    await db.commit()

    return session


# =========================================
# END SESSION
# =========================================
@router.post("/end/{session_id}")
async def end_session(
    session_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db)
):

    if not request.state.user:
        raise HTTPException(401, "Unauthorized")

    await agent_permission_service.require_agent(
        db,
        request.state.user["id"]
    )

    session = await market_live_session_service.end_session(
        db=db,
        session_id=session_id,
        user_id=request.state.user["id"]
    )

    await db.commit()

    return session


# =========================================
# ACTIVE LIVE SESSIONS
# =========================================
@router.get("/live")
async def get_live_sessions(
    db: AsyncSession = Depends(get_db)
):

    sessions = (
        await market_live_session_service.get_active_sessions(
            db=db
        )
    )

    return sessions


# =========================================
# MARKET SESSIONS
# =========================================
@router.get("/market/{market_id}")
async def get_market_sessions(
    market_id: str,
    db: AsyncSession = Depends(get_db)
):

    sessions = (
        await market_live_session_service.get_market_sessions(
            db=db,
            market_id=market_id
        )
    )

    return sessions


# =========================================
# STREAM TOKEN
# =========================================
@router.get("/{session_id}/token")
async def get_stream_token(
    session_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db)
):

    if not request.state.user:
        raise HTTPException(
            401,
            "Unauthorized"
        )

    session = await db.get(
        MarketLiveSession,
        session_id
    )

    if not session:
        raise HTTPException(
            404,
            "Live session not found"
        )

    return await streaming_service.generate_token(
        session.stream_channel,
        request.state.user["id"]
    )


# =========================================
# INCREMENT VIEWERS
# =========================================
@router.post("/{session_id}/viewer/join")
async def join_live_session(
    session_id: str,
    db: AsyncSession = Depends(get_db)
):

    session = (
        await market_live_session_service.increment_viewers(
            db=db,
            session_id=session_id
        )
    )

    await db.commit()

    return {
        "viewer_count": session.viewer_count
    }


# =========================================
# DECREMENT VIEWERS
# =========================================
@router.post("/{session_id}/viewer/leave")
async def leave_live_session(
    session_id: str,
    db: AsyncSession = Depends(get_db)
):

    session = (
        await market_live_session_service.decrement_viewers(
            db=db,
            session_id=session_id
        )
    )

    await db.commit()

    return {
        "viewer_count": session.viewer_count
    }