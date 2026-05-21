from sqlalchemy import Column, Integer, Float, ForeignKey
from db.base import Base


class Wallet(Base):
    __tablename__ = "wallets"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))

    balance = Column(Float, default=0.0)
    locked_balance = Column(Float, default=0.0)   # escrow