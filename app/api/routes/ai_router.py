from fastapi import APIRouter, Depends, Request, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.rate_limit_service import (
    rate_limit_service
)

from app.services.recommendation_learning_service import (
recommendation_learning_service
)

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

=====================================================

REQUEST SCHEMAS

=====================================================

class AIChatRequest(BaseModel):
message: str

class RecommendationActionRequest(BaseModel):
recommendation_id: str

=====================================================

AI CHAT

=====================================================

@router.post("/chat")
async def chat(
    payload: AIChatRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):

    await rate_limit_service.check_limit(
        key=f"ai_chat:.     {request.state.user['id']}",
        limit=30,
        ttl=60
    )
    return await ai_service.process_message(
        db=db,
        user_id=request.state.user["id"],
        message=payload.message,
    )

=====================================================

GET MY CONVERSATIONS

=====================================================

@router.get("/conversations")
async def get_my_conversations(
request: Request,
db: AsyncSession = Depends(get_db),
):

user_id = request.state.user["id"]

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

=====================================================

GET SINGLE CONVERSATION

=====================================================

@router.get("/conversation/{conversation_id}")
async def get_conversation_detail(
conversation_id: str,
request: Request,
db: AsyncSession = Depends(get_db),
):

conversation = await ai_logger.get_conversation(
    db=db,
    conversation_id=conversation_id,
)

if not conversation:
    raise HTTPException(
        status_code=404,
        detail="Conversation not found"
    )

if conversation.user_id != request.state.user["id"]:
    raise HTTPException(
        status_code=403,
        detail="Access denied"
    )

return conversation

=====================================================

GET MESSAGES

=====================================================

@router.get("/messages/{conversation_id}")
async def get_messages(
conversation_id: str,
request: Request,
db: AsyncSession = Depends(get_db),
):

conversation = await ai_logger.get_conversation(
    db=db,
    conversation_id=conversation_id,
)

if not conversation:
    raise HTTPException(
        status_code=404,
        detail="Conversation not found"
    )

if conversation.user_id != request.state.user["id"]:
    raise HTTPException(
        status_code=403,
        detail="Access denied"
    )

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

=====================================================

DELETE CONVERSATION

=====================================================

@router.delete("/conversation/{conversation_id}")
async def delete_conversation(
conversation_id: str,
request: Request,
db: AsyncSession = Depends(get_db),
):

conversation = await ai_logger.get_conversation(
    db=db,
    conversation_id=conversation_id,
)

if not conversation:
    raise HTTPException(
        status_code=404,
        detail="Conversation not found"
    )

if conversation.user_id != request.state.user["id"]:
    raise HTTPException(
        status_code=403,
        detail="Access denied"
    )

await ai_logger.delete_conversation(
    db=db,
    conversation_id=conversation_id,
)

await db.commit()

return {
    "success": True
}

=====================================================

CLEAR MY HISTORY

=====================================================

@router.delete("/history")
async def clear_user_history(
request: Request,
db: AsyncSession = Depends(get_db),
):

await ai_logger.clear_user_history(
    db=db,
    user_id=request.state.user["id"],
)

await db.commit()

return {
    "success": True
}

=====================================================

RECOMMENDATION CLICK TRACKING

=====================================================

@router.post("/recommendations/click")
async def click_recommendation(
    payload: RecommendationActionRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    rec = await db.get(
        AIProductRecommendation,
        payload.recommendation_id,
    )

    if not rec:
        raise HTTPException(
            status_code=404,
            detail="Recommendation not found"
        )

    conversation = await ai_logger.get_conversation(
        db=db,
        conversation_id=rec.conversation_id
    )

    if (
        not conversation
        or conversation.user_id != request.state.user["id"]
    ):
        raise HTTPException(
            status_code=403,
            detail="Access denied"
        )

    await recommendation_learning_service.process_click(
        db,
        rec
    )

    await db.commit()

    return {"status": "ok"}


=====================================================

RECOMMENDATION ADD TO CART TRACKING

=====================================================

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
    await recommendation_learning_service.process_add_to_cart(
        db,
        rec
    )

await db.commit()

return {"status": "ok"}
=====================================================

RECOMMENDATION PURCHASE TRACKING

=====================================================

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
    await recommendation_learning_service.process_purchase(
        db,
        rec
    )

await db.commit()

return {"status": "ok"}