from sqlalchemy import Column, Integer, ForeignKey, Enum, Float
from db.base import Base
import enum


class MembershipStatus(str, enum.Enum):
    pending = "pending"
    active = "active"
    failed = "failed"
    refunded = "refunded"


class Membership(Base):
    __tablename__ = "memberships"

    id = Column(Integer, primary_key=True)

    user_id = Column(Integer, ForeignKey("users.id"))
    cooperative_id = Column(Integer, ForeignKey("cooperatives.id"))

    contribution_amount = Column(Float)

    status = Column(Enum(MembershipStatus), default=MembershipStatus.pending)