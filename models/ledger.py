from sqlalchemy import Column, Integer, Float, String, DateTime
from sqlalchemy.sql import func
from db.base import Base


class Ledger(Base):
    __tablename__ = "ledger"

    id = Column(Integer, primary_key=True)

    user_id = Column(Integer)
    cooperative_id = Column(Integer, nullable=True)

    type = Column(String)  # contribution | refund | payment | escrow_hold
    amount = Column(Float)

    status = Column(String)  # success | failed

    created_at = Column(DateTime(timezone=True), server_default=func.now())

# Ledger Entry

class LedgerEntry(Base):
    __tablename__ = "ledger_entries"

    id = Column(Integer, primary_key=True)

    user_id = Column(Integer, index=True)
    cooperative_id = Column(Integer, index=True)

    amount = Column(Float)
    type = Column(String)  # escrow_hold, release, refund, payment

    reference = Column(String)
    status = Column(String)

    created_at = Column(DateTime(timezone=True), server_default=func.now())