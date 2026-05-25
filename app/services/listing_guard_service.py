from fastapi import HTTPException


class ListingGuardService:

    # =========================
    # ROLE CHECK
    # =========================
    def enforce_listing_permission(self, roles: list):

        if "admin" in roles:
            return True

        if "agent" in roles:
            return True

        raise HTTPException(
            status_code=403,
            detail="Only agents or admins can create listings"
        )


listing_guard_service = ListingGuardService()