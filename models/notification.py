from sqlalchemy import Column, Integer, String, Enum, ForeignKey, DateTime
from sqlalchemy.sql import func
from db.base import Base
import enum


class NotificationType(str, enum.Enum):
    info = "info"
    success = "success"
    warning = "warning"
    ai = "ai"


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True)

    user_id = Column(Integer, index=True)
    cooperative_id = Column(Integer, nullable=True)

    title = Column(String)
    message = Column(String)

    type = Column(Enum(NotificationType), default=NotificationType.info)

    created_at = Column(DateTime(timezone=True), server_default=func.now())