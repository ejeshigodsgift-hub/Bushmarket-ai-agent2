import uuid
from sqlalchemy import String, ForeignKey, Numeric, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class CooperativePartialProcurement(Base):

    __tablename__ = "cooperative_partial_procurements"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    cooperative_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("cooperatives.id"),
        nullable=False
    )

    member_id: Mapped[str] = mapped_column(String(36), nullable=False)

    vote: Mapped[bool] = mapped_column(Boolean)
    """
    True → proceed partial procurement
    False → extend lifecycle
    """

    quantity_share: Mapped[float] = mapped_column(Numeric(18, 2), default=0)