from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db

from app.services.ai_service import ai_service
from app.services.ai_logger import ai_logger

from app.db.models.ai_message import AIMessage
from app.db.models.ai_conversation import AIConversation
from app.db.models.ai_product_recommendation import (
    AIProductRecommendation,
)

router = APIRouter(
    prefix="/ai",
    tags=["AI"]
)


# =====================================================
# REQUEST SCHEMAS
# =====================================================

class AIChatRequest(BaseModel):
    user_id: str
    message: str


class RecommendationActionRequest(BaseModel):
    recommendation_id: str


# =====================================================
# AI CHAT
# =====================================================

@router.post("/chat")
async def chat(
    payload: AIChatRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    return await ai_service.process_message(
        db=db,
        user_id=request.state.user["id"],
        message=payload.message,
    )


# =====================================================
# GET USER CONVERSATIONS
# =====================================================

@router.get("/conversation/{user_id}")
async def get_conversation(
    user_id: str,
    db: AsyncSession = Depends(get_db),
):

    stmt = (
        select(AIConversation)
        .where(
            AIConversation.user_id == user_id
        )
        .order_by(
            AIConversation.created_at.desc()
        )
    )

    result = await db.execute(stmt)

    return result.scalars().all()


# =====================================================
# GET SINGLE CONVERSATION
# =====================================================

@router.get("/conversation/detail/{conversation_id}")
async def get_conversation_detail(
    conversation_id: str,
    db: AsyncSession = Depends(get_db),
):

    return await ai_logger.get_conversation(
        db=db,
        conversation_id=conversation_id,
    )


# =====================================================
# GET USER CONVERSATIONS (LOGGER VERSION)
# =====================================================

@router.get("/conversation/user/{user_id}")
async def get_user_conversations(
    user_id: str,
    db: AsyncSession = Depends(get_db),
):

    return await ai_logger.get_user_conversations(
        db=db,
        user_id=user_id,
    )


# =====================================================
# GET MESSAGES
# =====================================================

@router.get("/messages/{conversation_id}")
async def get_messages(
    conversation_id: str,
    db: AsyncSession = Depends(get_db),
):

    stmt = (
        select(AIMessage)
        .where(
            AIMessage.conversation_id == conversation_id
        )
        .order_by(
            AIMessage.created_at.asc()
        )
    )

    result = await db.execute(stmt)

    return result.scalars().all()


# =====================================================
# DELETE CONVERSATION
# =====================================================

@router.delete("/conversation/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    db: AsyncSession = Depends(get_db),
):

    await ai_logger.delete_conversation(
        db=db,
        conversation_id=conversation_id,
    )

    await db.commit()

    return {
        "success": True
    }


# =====================================================
# CLEAR USER HISTORY
# =====================================================

@router.delete("/conversation/user/{user_id}")
async def clear_user_history(
    user_id: str,
    db: AsyncSession = Depends(get_db),
):

    await ai_logger.clear_user_history(
        db=db,
        user_id=user_id,
    )

    await db.commit()

    return {
        "success": True
    }


# =====================================================
# RECOMMENDATION CLICK TRACKING
# =====================================================

@router.post("/recommendations/click")
async def click_recommendation(
    payload: RecommendationActionRequest,
    db: AsyncSession = Depends(get_db),
):

    rec = await db.get(
        AIProductRecommendation,
        payload.recommendation_id,
    )

    if rec:
        rec.clicked = True

    await db.commit()

    return {
        "status": "ok"
    }


# =====================================================
# RECOMMENDATION ADD TO CART TRACKING
# =====================================================

@router.post("/recommendations/cart")
async def add_to_cart_recommendation(
    payload: RecommendationActionRequest,
    db: AsyncSession = Depends(get_db),
):

    rec = await db.get(
        AIProductRecommendation,
        payload.recommendation_id,
    )

    if rec:
        rec.added_to_cart = True

    await db.commit()

    return {
        "status": "ok"
    }


# =====================================================
# RECOMMENDATION PURCHASE TRACKING
# =====================================================

@router.post("/recommendations/purchase")
async def purchase_recommendation(
    payload: RecommendationActionRequest,
    db: AsyncSession = Depends(get_db),
):

    rec = await db.get(
        AIProductRecommendation,
        payload.recommendation_id,
    )

    if rec:
        rec.purchased = True

    await db.commit()

    return {
        "status": "ok"
    }