from app.db.models.audit_log import AuditLog


class AuditService:

    def log(self, db, user_id: str, action: str, entity_type: str, entity_id: str, metadata: dict, ip: str):
        log = AuditLog(
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            metadata=metadata,
            ip_address=ip
        )

        db.add(log)
        db.commit()