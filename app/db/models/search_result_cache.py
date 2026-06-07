import uuid
from sqlalchemy import String, DateTime, Text, func, Index
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class SearchResultCache(Base):
    __tablename__ = "search_result_cache"

    # =========================
    # PRIMARY KEY
    # =========================
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    # =========================
    # CACHE KEY
    # =========================
    query_hash: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True
    )

    query_text: Mapped[str] = mapped_column(
        String,
        index=True
    )

    # =========================
    # STORED RESULTS
    # =========================
    result_json: Mapped[str] = mapped_column(
        Text
    )

    total_results: Mapped[int] = mapped_column(
        index=True,
        default=0
    )

    # =========================
    # EXPIRY CONTROL
    # =========================
    expires_at: Mapped[str] = mapped_column(
        DateTime(timezone=True),
        index=True
    )

    # =========================
    # TIMESTAMP
    # =========================
    created_at: Mapped[str] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )