# app/services/shopper_profile_service.py

class ShopperProfileService:

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

    async def get_profile(self, db: AsyncSession, user_id: str):
        result = await db.execute(
            select(ShopperProfile).where(
                ShopperProfile.user_id == user_id
            )
        )
        return result.scalar_one_or_none()

    async def update_profile(
        self,
        db: AsyncSession,
        user_id: str,
        data: dict
    ):
        profile = await self.get_profile(db, user_id)

        if not profile:
            return None

        for k, v in data.items():
            setattr(profile, k, v)

        await db.flush()
        return profile