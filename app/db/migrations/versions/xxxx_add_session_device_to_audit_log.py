"""add session_id and device_id to audit_log

Revision ID: add_session_device_audit
Revises: previous_revision_id
Create Date: 2026-06-01
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic
revision = "add_session_device_audit"
down_revision = None  # replace with your last migration id
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "audit_logs",
        sa.Column("session_id", sa.String(), nullable=True)
    )

    op.add_column(
        "audit_logs",
        sa.Column("device_id", sa.String(), nullable=True)
    )


def downgrade():
    op.drop_column("audit_logs", "device_id")
    op.drop_column("audit_logs", "session_id")