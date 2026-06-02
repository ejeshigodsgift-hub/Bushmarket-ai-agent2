from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.models.shopper_profile import ShopperProfile


class ShopperPreferenceService:

    # =========================================
    # CREATE DEFAULT PROFILE
    # =========================================
    async def create_default_profile(
        self,
        db: AsyncSession,
        user_id: str,
        email: str | None = None,
        phone: str | None = None
    ):

        profile = ShopperProfile(
            user_id=user_id,
            email=email,
            phone=phone,
            preferred_categories=[],
            location=None
        )

        db.add(profile)
        await db.flush()

        return profile

    # =========================================
    # GET PROFILE
    # =========================================
    async def get_profile(self, db: AsyncSession, user_id: str):

        result = await db.execute(
            select(ShopperProfile).where(
                ShopperProfile.user_id == user_id
            )
        )

        return result.scalar_one_or_none()

    # =========================================
    # UPDATE PROFILE (UPGRADE SYSTEM)
    # =========================================
    async def update_profile(
        self,
        db: AsyncSession,
        user_id: str,
        data: dict
    ):

        profile = await self.get_profile(db, user_id)

        if not profile:
            return None

        if "email" in data:
            profile.email = data["email"]

        if "phone" in data:
            profile.phone = data["phone"]

        if "location" in data:
            profile.location = data["location"]

        if "preferred_categories" in data:
            profile.preferred_categories = data["preferred_categories"]

        await db.commit()
        await db.refresh(profile)

        return profile


shopper_preference_service = ShopperPreferenceService()