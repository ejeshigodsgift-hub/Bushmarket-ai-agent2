from app.db.models.role import Role


class PermissionService:

    ROLE_MAP = {
        "admin": ["*"],
        "agent": ["sourcing", "delivery", "tasks"],
        "cooperative_creator": ["create_cooperative"],
        "member": ["join_cooperative"],
        "shopper": ["shop"]
    }

    def has_permission(self, roles: list, action: str):
        for role in roles:
            permissions = self.ROLE_MAP.get(role, [])
            if "*" in permissions or action in permissions:
                return True
        return False