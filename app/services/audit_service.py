from sqlalchemy.orm import Session as DBSession
from app.db.models.audit_log import AuditLog
from datetime import datetime, timezone


class AuditService:

    def log(
        self,
        db: DBSession,
        user_id: str,
        action: str,
        entity_type: str,
        entity_id: str | None,
        metadata: dict,
        ip: str | None = None,
        session_id: str | None = None,
        device_id: str | None = None
    ):

        log = AuditLog(

            user_id=user_id,

            action=action,
            entity_type=entity_type,
            entity_id=entity_id,

            event_data=metadata,   # FIXED naming consistency

            ip_address=ip,

            created_at=datetime.now(timezone.utc)
        )

        db.add(log)
        db.commit()
        db.refresh(log)

        return log