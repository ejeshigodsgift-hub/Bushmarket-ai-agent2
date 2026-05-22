import uuid
from sqlalchemy import Column, String, Boolean, TIMESTAMP, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
from app.db.base import Base


class ApiKey(Base):
    __tablename__ = "api_keys"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))

    key_hash = Column(String, unique=True, nullable=False)

    is_active = Column(Boolean, default=True)

    created_at = Column(TIMESTAMP, default=datetime.utcnow)