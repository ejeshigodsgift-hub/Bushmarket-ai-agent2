from sqlalchemy import Column, Integer, Float, String, DateTime
from sqlalchemy.sql import func
from db.base import Base


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True)

    user_id = Column(Integer)
    cooperative_id = Column(Integer)

    amount = Column(Float)
    status = Column(String)  # pending | success | failed
    type = Column(String)    # payment | refund | contribution

    created_at = Column(DateTime(timezone=True), server_default=func.now())