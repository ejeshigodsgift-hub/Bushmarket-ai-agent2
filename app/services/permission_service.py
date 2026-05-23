from fastapi import HTTPException


class PermissionService:

    ROLE_PERMISSIONS = {
        "admin": ["*"],

        "shopper": ["shop_products"],

        "member": ["join_cooperative"],

        "cooperative_creator": ["create_cooperative"],

        "agent": ["product_sourcing", "delivery_tasks", "tasks"]
    }

    def validate_permission(self, roles: list, action: str) -> bool:

        for role in roles:
            permissions = self.ROLE_PERMISSIONS.get(role, [])

            if "*" in permissions:
                return True

            if action in permissions:
                return True

        raise HTTPException(
            status_code=403,
            detail=f"Permission denied for action: {action}"
        )

    # OPTIONAL helper (only if needed internally)
    def has_permission(self, roles: list, action: str) -> bool:
        try:
            return self.validate_permission(roles, action)
        except HTTPException:
            return False