"""drop legacy session tables

Revision ID: 20260904_0012
Revises: 20260904_0011
Create Date: 2026-09-04 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20260904_0012"
down_revision: Union[str, None] = "20260904_0011"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_index(op.f("ix_room_pointers_session_id"), table_name="room_pointers")
    op.drop_table("room_pointers")
    op.drop_index(op.f("ix_sessions_session_id"), table_name="sessions")
    op.drop_table("sessions")


def downgrade() -> None:
    op.create_table(
        "sessions",
        sa.Column("session_id", sa.Integer(), nullable=False),
        sa.Column("session_key", sa.Text(), nullable=False),
        sa.Column("room_id", sa.Text(), nullable=False),
        sa.Column("updated_at", sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint("session_id"),
    )
    op.create_index(op.f("ix_sessions_session_id"), "sessions", ["session_id"], unique=False)

    op.create_table(
        "room_pointers",
        sa.Column("room_id", sa.Text(), nullable=False),
        sa.Column("session_id", sa.Integer(), nullable=False),
        sa.Column("updated_at", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(["session_id"], ["sessions.session_id"]),
        sa.PrimaryKeyConstraint("room_id"),
    )
    op.create_index(op.f("ix_room_pointers_session_id"), "room_pointers", ["session_id"], unique=False)
