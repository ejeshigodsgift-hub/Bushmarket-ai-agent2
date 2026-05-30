from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.role import Role

from app.services.outbox_service import outbox_service


class AgentService:

    async def approve_agent(
        self,
        db: AsyncSession,
        user_id: str,
        admin_id: str
    ):

        existing = await db.execute(
            select(Role).where(
                Role.user_id == user_id,
                Role.role == "agent"
            )
        )

        role_exists = existing.scalar_one_or_none()

        if role_exists:
            return role_exists

        role = Role(
            user_id=user_id,
            role="agent"
        )

        db.add(role)

        # =========================================
        # OUTBOX EVENT
        # =========================================

        await outbox_service.queue_event(
            db=db,
            topic="agent.approved",
            payload={
                "user_id": user_id,
                "admin_id": admin_id,
                "role": "agent"
            }
        )

        await db.commit()

        await db.refresh(role)

        return role