from fastapi import APIRouter
from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.db.models.notification import Notification

router = APIRouter(
    prefix="/notifications",
    tags=["Notifications"]
)


@router.get("/")
async def get_notifications(
    user_id: str,
    db: AsyncSession = Depends(get_db)
):

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



@router.get("/{notification_id}")
async def get_notification(
    notification_id: str,
    db: AsyncSession = Depends(get_db)
):

    stmt = (
        select(Notification)
        .where(
            Notification.id == notification_id
        )
        .limit(1)
    )

    result = await db.execute(stmt)

    notification = result.scalar_one_or_none()

    if not notification:
        return {
            "detail": "Notification not found"
        }

    return notification



@router.post("/{notification_id}/read")
async def mark_read(
    notification_id: str,
    db: AsyncSession = Depends(get_db)
):

    stmt = (
        select(Notification)
        .where(
            Notification.id == notification_id
        )
        .limit(1)
    )

    result = await db.execute(stmt)

    notification = result.scalar_one_or_none()

    if not notification:
        return {
            "detail": "Notification not found"
        }

    notification.is_read = True

    await db.commit()

    return {
        "status": "success"
    }


from sqlalchemy import update


@router.post("/read-all")
async def mark_all_read(
    user_id: str,
    db: AsyncSession = Depends(get_db)
):

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
        "status": "success"
    }
