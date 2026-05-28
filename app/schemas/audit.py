from datetime import datetime

from pydantic import BaseModel


class AuditLogResponse(BaseModel):

    id: str
    user_id: str
    action: str
    entity_type: str
    entity_id: str | None
    event_data: dict
    ip_address: str | None
    created_at: datetime