"""create message sessions table

Revision ID: 20260807_0005
Revises: 20260807_0004
Create Date: 2026-08-07 00:40:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "20260807_0005"
down_revision: Union[str, None] = "20260807_0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "message_sessions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("message_id", sa.Integer(), nullable=False),
        sa.Column("session_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["message_id"], ["message_logs.id"]),
        sa.ForeignKeyConstraint(["session_id"], ["sessions.session_id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("message_id", "session_id", name="uq_message_sessions_message_id_session_id"),
    )
    op.create_index(op.f("ix_message_sessions_id"), "message_sessions", ["id"], unique=False)
    op.create_index(op.f("ix_message_sessions_message_id"), "message_sessions", ["message_id"], unique=False)
    op.create_index(op.f("ix_message_sessions_session_id"), "message_sessions", ["session_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_message_sessions_session_id"), table_name="message_sessions")
    op.drop_index(op.f("ix_message_sessions_message_id"), table_name="message_sessions")
    op.drop_index(op.f("ix_message_sessions_id"), table_name="message_sessions")
    op.drop_table("message_sessions")
