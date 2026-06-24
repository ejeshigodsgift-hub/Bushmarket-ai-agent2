# =========================================
# FILE: app/api/notification.py
# =========================================

from fastapi import (
    APIRouter,
    Depends,
    Request,
    HTTPException
)

from sqlalchemy import (
    select,
    update
)

from sqlalchemy import func

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.db.models.notification import Notification

from app.services.notification_service import (
    notification_service
)

router = APIRouter(
    prefix="/notifications",
    tags=["Notifications"]
)


# =========================================
# GET MY NOTIFICATIONS
# =========================================
@router.get("/")
async def get_notifications(
    request: Request,
    db: AsyncSession = Depends(get_db)
):

    user = request.state.user

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Unauthorized"
        )

    user_id = user["id"]

    stmt = (
        select(Notification)
        .where(
            Notification.user_id == user_id
        )
        .order_by(
            Notification.created_at.desc()
        )
    )

    result = await db.execute(stmt)

    notifications = result.scalars().all()

    return notifications


# =========================================
# GET SINGLE NOTIFICATION
# =========================================
@router.get("/{notification_id}")
async def get_notification(
    notification_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db)
):

    user = request.state.user

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Unauthorized"
        )

    user_id = user["id"]

    stmt = (
        select(Notification)
        .where(
            Notification.id == notification_id,
            Notification.user_id == user_id
        )
        .limit(1)
    )

    result = await db.execute(stmt)

    notification = result.scalar_one_or_none()

    if not notification:
        raise HTTPException(
            status_code=404,
            detail="Notification not found"
        )

    return notification


# =========================================
# MARK SINGLE NOTIFICATION AS READ
# =========================================
@router.post("/{notification_id}/read")
async def mark_read(
    notification_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db)
):

    user = request.state.user

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Unauthorized"
        )

    user_id = user["id"]

    stmt = (
        select(Notification)
        .where(
            Notification.id == notification_id,
            Notification.user_id == user_id
        )
        .limit(1)
    )

    result = await db.execute(stmt)

    notification = result.scalar_one_or_none()

    if not notification:
        raise HTTPException(
            status_code=404,
            detail="Notification not found"
        )

    await notification_service.mark_read(
        db=db,
        notification=notification
    )

    await db.commit()

    return {
        "status": "success",
        "message": "Notification marked as read"
    }


# =========================================
# MARK ALL NOTIFICATIONS AS READ
# =========================================
@router.post("/read-all")
async def mark_all_read(
    request: Request,
    db: AsyncSession = Depends(get_db)
):

    user = request.state.user

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Unauthorized"
        )

    user_id = user["id"]

    await db.execute(
        update(Notification)
        .where(
            Notification.user_id == user_id,
            Notification.is_read.is_(False)
        )
        .values(
            is_read=True
        )
    )

    await db.commit()

    return {
        "status": "success",
        "message": "All notifications marked as read"
    }


# =========================================
# GET UNREAD COUNT
# =========================================
@router.get("/unread/count")
async def unread_count(
    request: Request,
    db: AsyncSession = Depends(get_db)
):

    user = request.state.user

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Unauthorized"
        )

    user_id = user["id"]

    stmt = (
        select(Notification)
        .where(
            Notification.user_id == user_id,
            Notification.is_read.is_(False)
        )
    )

    stmt = (
        select(func.count())
        .select_from(Notification)
        .where(
            Notification.user_id == user_id,
            Notification.is_read.is_(False)
        )
    )

    result = await db.execute(stmt)

    count = result.scalar_one()
    return {
        "unread_count": count
    }