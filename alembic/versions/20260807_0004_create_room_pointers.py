"""create room pointers table

Revision ID: 20260807_0004
Revises: 20260807_0003
Create Date: 2026-08-07 00:30:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "20260807_0004"
down_revision: Union[str, None] = "20260807_0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "room_pointers",
        sa.Column("room_id", sa.Text(), nullable=False),
        sa.Column("session_id", sa.Integer(), nullable=False),
        sa.Column("updated_at", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(["session_id"], ["sessions.session_id"]),
        sa.PrimaryKeyConstraint("room_id"),
    )
    op.create_index(op.f("ix_room_pointers_session_id"), "room_pointers", ["session_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_room_pointers_session_id"), table_name="room_pointers")
    op.drop_table("room_pointers")
