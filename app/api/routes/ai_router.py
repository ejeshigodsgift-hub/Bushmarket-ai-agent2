from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.services.ai_service import ai_service
from app.schemas.ai_schema import AIChatRequest

router = APIRouter(prefix="/ai", tags=["AI"])


@router.post("/chat")
async def chat(
    payload: AIChatRequest,
    db: AsyncSession = Depends(get_db)
):
    return await ai_service.process_message(
        db=db,
        user_id=payload.user_id,
        message=payload.message
    )