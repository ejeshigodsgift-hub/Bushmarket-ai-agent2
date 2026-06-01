from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.shopper_profile import ShopperProfile


class ShopperProfileService:

    # =========================================
    # AUTO CREATE PROFILE (ON SIGNUP)
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
            preferred_categories=None,
            location=None
        )

        db.add(profile)
        return profile

    # =========================================
    # GET PROFILE
    # =========================================
    async def get_profile(
        self,
        db: AsyncSession,
        user_id: str
    ):

        result = await db.execute(
            select(ShopperProfile).where(
                ShopperProfile.user_id == user_id
            )
        )

        return result.scalar_one_or_none()

    # =========================================
    # UPDATE PROFILE (UPGRADES)
    # =========================================
    async def update_profile(
        self,
        db: AsyncSession,
        user_id: str,
        data: dict
    ):

        result = await db.execute(
            select(ShopperProfile).where(
                ShopperProfile.user_id == user_id
            )
        )

        profile = result.scalar_one_or_none()

        if not profile:
            return None

        for key, value in data.items():
            if hasattr(profile, key):
                setattr(profile, key, value)

        return profile


shopper_profile_service = ShopperProfileService()