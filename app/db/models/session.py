import uuid
from sqlalchemy import Column, TIMESTAMP, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
from app.db.base import Base


class UserSession(Base):
    __tablename__ = "user_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))

    session_token = Column(String, unique=True, nullable=False)

    device_info = Column(String)
    ip_address = Column(String)

    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    expires_at = Column(TIMESTAMP)