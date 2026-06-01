from datetime import datetime, timezone

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import SessionLocal
from app.db.models.session import Session


async def cleanup_expired_sessions():

    async with SessionLocal() as db:

        try:
            now = datetime.now(timezone.utc)

            stmt = (
                update(Session)
                .where(Session.expires_at < now)
                .values(
                    is_active=False,
                    is_revoked=True,
                    revoked_at=now
                )
            )

            await db.execute(stmt)
            await db.commit()

        except Exception:
            await db.rollback()
            raise