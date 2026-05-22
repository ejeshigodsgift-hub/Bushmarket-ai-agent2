import uuid
from sqlalchemy import String, DateTime, ForeignKey, Boolean, func
from app.db.base import Base


class Session(Base):
    __tablename__ = "sessions"

    id = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))

    user_id = mapped_column(String, ForeignKey("users.id"), index=True)

    session_token = mapped_column(String, unique=True, index=True)
    refresh_token = mapped_column(String, unique=True)

    user_agent = mapped_column(String, nullable=True)
    ip_address = mapped_column(String, nullable=True)

    is_active = mapped_column(Boolean, default=True)

    expires_at = mapped_column(DateTime)

    created_at = mapped_column(DateTime, server_default=func.now())