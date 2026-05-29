# =========================================
# FILE: app/services/listing_guard_service.py
# =========================================

from fastapi import HTTPException


class ListingGuardService:

    """
    Centralized RBAC enforcement
    for listing operations.
    """

    # =========================================
    # CREATE LISTING ACCESS
    # =========================================
    async def enforce_create_permission(
        self,
        roles: list[str]
    ) -> bool:

        allowed_roles = {
            "admin",
            "agent"
        }

        if not set(roles).intersection(allowed_roles):

            raise HTTPException(
                status_code=403,
                detail=(
                    "Only approved agents "
                    "or admins can create listings"
                )
            )

        return True

    # =========================================
    # ADMIN ACCESS
    # =========================================
    async def enforce_admin_access(
        self,
        roles: list[str]
    ) -> bool:

        if "admin" not in roles:

            raise HTTPException(
                status_code=403,
                detail="Admin access required"
            )

        return True


listing_guard_service = ListingGuardService()