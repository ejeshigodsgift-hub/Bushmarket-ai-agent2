from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.role import Role


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

        await db.commit()
        await db.refresh(role)

        return role