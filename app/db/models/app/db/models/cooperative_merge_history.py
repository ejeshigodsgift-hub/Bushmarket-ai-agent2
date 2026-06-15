import uuid
from datetime import datetime
from sqlalchemy import (
String,
DateTime,
ForeignKey,
func
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

class CooperativeMergeHistory(Base):
"""
Audit trail for executed cooperative merges.
"""

__tablename__ = "cooperative_merge_history"

# =========================
# PRIMARY KEY
# =========================
id: Mapped[str] = mapped_column(
    String(36),
    primary_key=True,
    default=lambda: str(uuid.uuid4())
)

# =========================
# REFERENCES
# =========================
proposal_id: Mapped[str] = mapped_column(
    String(36),
    ForeignKey("cooperative_merge_proposals.id"),
    nullable=False
)

merged_procurement_id: Mapped[str] = mapped_column(
    String(36),
    ForeignKey("cooperative_procurements.id"),
    nullable=False
)

# store list of cooperatives involved in merge
cooperative_ids: Mapped[list] = mapped_column(
    JSONB,
    nullable=False
)

# =========================
# TIMESTAMPS
# =========================
executed_at: Mapped[datetime] = mapped_column(
    DateTime(timezone=True),
    nullable=False
)

created_at: Mapped[datetime] = mapped_column(
    DateTime(timezone=True),
    server_default=func.now(),
    nullable=False
)