import uuid
from sqlalchemy import String, ForeignKey, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class Role(Base):
    __tablename__ = "user_roles"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"))

    role: Mapped[str] = mapped_column(String(50))
    created_at = mapped_column(DateTime, server_default=func.now())

    user = relationship("User", back_populates="roles")