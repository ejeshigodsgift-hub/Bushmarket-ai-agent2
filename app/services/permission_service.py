from fastapi import HTTPException


class PermissionService:

    ROLE_PERMISSIONS = {

        # =========================
        # SYSTEM ADMIN
        # =========================
        "admin": ["*"],

        # =========================
        # SHOPPER
        # =========================
        "shopper": [
            "shop_products",
            "view_products"
        ],

        # =========================
        # COOPERATIVE MEMBER
        # =========================
        "member": [
            "join_cooperative",
            "view_cooperative"
        ],

        # =========================
        # COOPERATIVE CREATOR
        # =========================
        "cooperative_creator": [
            "create_cooperative",
            "manage_cooperative"
        ],

        # =========================
        # AGENT (FIELD OPERATIONS)
        # =========================
        "agent": [
            "product_sourcing",
            "delivery_tasks",
            "task_execution"
        ]
    }

    # =========================
    # STRICT VALIDATION (RAISES ERROR)
    # =========================
    def validate_permission(self, roles: list, action: str) -> bool:

        for role in roles:

            permissions = self.ROLE_PERMISSIONS.get(role, [])

            # ADMIN OVERRIDE
            if "*" in permissions:
                return True

            if action in permissions:
                return True

        raise HTTPException(
            status_code=403,
            detail=f"Permission denied for action: {action}"
        )

    # =========================
    # SAFE CHECK (NO THROW)
    # =========================
    def has_permission(self, roles: list, action: str) -> bool:

        try:
            self.validate_permission(roles, action)
            return True

        except HTTPException:
            return False