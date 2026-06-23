

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.listing_admin_activity import ListingAdminActivity

class ListingAdminActivityService:

async def log(
    self,
    db: AsyncSession,
    listing_id: str,
    admin_id: str,
    action_type: str,
    activity_note: str | None = None,
    ip: str | None = None,
    is_system_generated: bool = False
):

    activity = ListingAdminActivity(
        listing_id=listing_id,
        admin_id=admin_id,
        action_type=action_type,
        activity_note=activity_note,
        ip_address=ip,
        is_system_generated=is_system_generated
    )

    db.add(activity)
    await db.flush()

    return activity

async def log_listing_published(
    self,
    db: AsyncSession,
    listing_id: str,
    admin_id: str,
    ip: str | None = None
):
    return await self.log(
        db=db,
        listing_id=listing_id,
        admin_id=admin_id,
        action_type="listing_published",
        activity_note="Listing published",
        ip=ip
    )

async def log_inventory_updated(
    self,
    db: AsyncSession,
    listing_id: str,
    admin_id: str,
    quantity: int,
    ip: str | None = None
):
    return await self.log(
        db=db,
        listing_id=listing_id,
        admin_id=admin_id,
        action_type="inventory_updated",
        activity_note=f"Inventory adjusted by {quantity}",
        ip=ip
    )

async def log_listing_approved(
    self,
    db: AsyncSession,
    listing_id: str,
    admin_id: str,
    ip: str | None = None
):
    return await self.log(
        db=db,
        listing_id=listing_id,
        admin_id=admin_id,
        action_type="admin_approved",
        activity_note="Listing approved",
        ip=ip
    )

async def log_listing_rejected(
    self,
    db: AsyncSession,
    listing_id: str,
    admin_id: str,
    reason: str | None = None,
    ip: str | None = None
):
    return await self.log(
        db=db,
        listing_id=listing_id,
        admin_id=admin_id,
        action_type="admin_rejected",
        activity_note=reason or "Listing rejected",
        ip=ip
    )

listing_admin_activity_service = ListingAdminActivityService()