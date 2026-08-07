"""create sessions table

Revision ID: 20260807_0003
Revises: 20260807_0002
Create Date: 2026-08-07 00:20:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "20260807_0003"
down_revision: Union[str, None] = "20260807_0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "sessions",
        sa.Column("session_id", sa.Integer(), nullable=False),
        sa.Column("session_key", sa.Text(), nullable=False),
        sa.Column("room_id", sa.Text(), nullable=False),
        sa.Column("updated_at", sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint("session_id"),
    )
    op.create_index(op.f("ix_sessions_session_id"), "sessions", ["session_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_sessions_session_id"), table_name="sessions")
    op.drop_table("sessions")
