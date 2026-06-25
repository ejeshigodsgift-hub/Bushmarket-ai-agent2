import uuid
from sqlalchemy import Integer

from sqlalchemy import (
    String,
    Boolean,
    ForeignKey,
    DateTime,
    func
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column
)

from app.db.base import Base


class MarketLiveSession(Base):

    __tablename__ = "market_live_sessions"

    id: Mapped[str] = mapped_column(
        String,
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    market_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("market_locations.id"),
        nullable=False
    )

    agent_user_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("users.id"),
        nullable=False
    )

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    stream_channel: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True
    )

    is_live: Mapped[bool] = mapped_column(
        Boolean,
        default=True
    )

    started_at: Mapped[DateTime] = mapped_column(
        DateTime,
        server_default=func.now()
    )

    ended_at: Mapped[DateTime | None] = mapped_column(
        DateTime,
        nullable=True
    )

    

    viewer_count: Mapped[int] =  mapped_column(
        Integer,
        nullable=False,
        default=0
    )

    stream_status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="live"
    )
    # scheduled | live | ended

    thumbnail_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True
    )