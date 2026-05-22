import uuid
from sqlalchemy import String, DateTime, Boolean, func
from app.db.base import Base


class APIKey(Base):
    __tablename__ = "api_keys"

    id = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))

    key_hash = mapped_column(String, unique=True, index=True)

    owner_type = mapped_column(String)  # supplier | system | agent
    owner_id = mapped_column(String)

    is_active = mapped_column(Boolean, default=True)

    created_at = mapped_column(DateTime, server_default=func.now())
    expires_at = mapped_column(DateTime, nullable=True)