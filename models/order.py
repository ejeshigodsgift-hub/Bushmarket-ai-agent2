from sqlalchemy import Column, Integer, String, Float, Enum, ForeignKey
from db.base import Base
import enum


class OrderStatus(str, enum.Enum):
    pending = "pending"
    processing = "processing"
    completed = "completed"
    failed = "failed"
    partial = "partial"


class CooperativeOrder(Base):
    __tablename__ = "cooperative_orders"

    id = Column(Integer, primary_key=True)

    cooperative_id = Column(Integer, index=True)
    product_id = Column(String)

    total_quantity = Column(Integer)
    total_amount = Column(Float)

    status = Column(Enum(OrderStatus), default=OrderStatus.pending)