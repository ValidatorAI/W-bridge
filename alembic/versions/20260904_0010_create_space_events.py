"""create space events

Revision ID: 20260904_0010
Revises: 20260904_0009
Create Date: 2026-09-04 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "20260904_0010"
down_revision: Union[str, None] = "20260813_0009"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "space_events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("space_event_id", sa.String(length=255), nullable=True),
        sa.Column("event_type", sa.String(length=255), nullable=True),
        sa.Column("event_id", sa.String(length=255), nullable=True),
        sa.Column("group_id", sa.String(length=255), nullable=True),
        sa.Column("event_data", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.String(length=255), nullable=True),
        sa.Column("stored_date", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("sent_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("result", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_space_events_id"), "space_events", ["id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_space_events_id"), table_name="space_events")
    op.drop_table("space_events")
