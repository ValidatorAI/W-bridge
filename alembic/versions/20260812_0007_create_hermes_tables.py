"""create hermes tables

Revision ID: 20260812_0007
Revises: 20260807_0006
Create Date: 2026-08-12 00:10:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "20260812_0007"
down_revision: Union[str, None] = "20260807_0006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "hermes_sessions",
        sa.Column("id", sa.String(length=255), nullable=False),
        sa.Column("is_forked", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("parent", sa.String(length=255), nullable=True),
        sa.Column("session_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["session_id"], ["sessions.session_id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_hermes_sessions_session_id"), "hermes_sessions", ["session_id"], unique=False)

    op.create_table(
        "hermess_messages",
        sa.Column("hermes_message_id", sa.String(length=255), nullable=False),
        sa.Column("message_id", sa.Integer(), nullable=False),
        sa.Column("is_bot_reply", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("hermes_message_id"),
    )


def downgrade() -> None:
    op.drop_table("hermess_messages")

    op.drop_index(op.f("ix_hermes_sessions_session_id"), table_name="hermes_sessions")
    op.drop_table("hermes_sessions")
