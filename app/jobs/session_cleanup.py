from datetime import datetime, timezone

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import SessionLocal
from app.db.models.session import Session


async def cleanup_expired_sessions():

    async with SessionLocal() as db:

        try:
            stmt = delete(Session).where(
                Session.expires_at < datetime.now(timezone.utc)
            )

            await db.execute(stmt)
            await db.commit()

        except Exception:
            await db.rollback()
            raise