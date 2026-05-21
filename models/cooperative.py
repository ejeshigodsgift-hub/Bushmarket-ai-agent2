from sqlalchemy import Column, String, Integer, Float, Enum, DateTime, ForeignKey
from sqlalchemy.sql import func
from db.base import Base
import enum


class CoopStatus(str, enum.Enum):
    draft = "draft"
    active = "active"
    funded = "funded"
    purchasing = "purchasing"
    closed = "closed"
    expired = "expired"


class Cooperative(Base):
    __tablename__ = "cooperatives"

    id = Column(Integer, primary_key=True)
    creator_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    product_id = Column(String, index=True)
    category = Column(String, index=True)

    quantity_target = Column(Integer)
    member_target = Column(Integer)

    contribution_amount = Column(Float)
    funding_target = Column(Float)

    lifespan_days = Column(Integer, default=60)

    status = Column(Enum(CoopStatus), default=CoopStatus.draft)

    total_pool = Column(Float, default=0)

    created_at = Column(DateTime(timezone=True), server_default=func.now())