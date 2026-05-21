from sqlalchemy import Column, Integer, String, Enum, ForeignKey
from db.base import Base
import enum


class DeliveryStatus(str, enum.Enum):
    pending = "pending"
    shipped = "shipped"
    delivered = "delivered"
    failed = "failed"


class Delivery(Base):
    __tablename__ = "deliveries"

    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey("cooperative_orders.id"))
    cooperative_id = Column(Integer)

    user_id = Column(Integer)
    status = Column(Enum(DeliveryStatus), default=DeliveryStatus.pending)

    tracking_code = Column(String)