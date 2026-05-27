from datetime import datetime, timezone

from sqlalchemy import delete

from app.db.session import SessionLocal
from app.db.models.session import Session


async def cleanup_expired_sessions():

    async with SessionLocal() as db:

        await db.execute(
            delete(Session).where(
                Session.expires_at < datetime.now(
                    timezone.utc
                )
            )
        )

        await db.commit()