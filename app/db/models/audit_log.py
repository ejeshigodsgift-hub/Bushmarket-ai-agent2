import uuid
from sqlalchemy import String, DateTime, func, JSON
from app.db.base import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))

    user_id = mapped_column(String, index=True)

    action = mapped_column(String(100))
    entity_type = mapped_column(String(100))
    entity_id = mapped_column(String, nullable=True)

    metadata = mapped_column(JSON)

    ip_address = mapped_column(String)
    created_at = mapped_column(DateTime, server_default=func.now())