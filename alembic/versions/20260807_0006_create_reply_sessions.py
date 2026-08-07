"""create reply sessions table

Revision ID: 20260807_0006
Revises: 20260807_0005
Create Date: 2026-08-07 00:50:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "20260807_0006"
down_revision: Union[str, None] = "20260807_0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "reply_sessions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("reply_id", sa.Integer(), nullable=False),
        sa.Column("session_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["reply_id"], ["bot_replies.id"]),
        sa.ForeignKeyConstraint(["session_id"], ["sessions.session_id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("reply_id", "session_id", name="uq_reply_sessions_reply_id_session_id"),
    )
    op.create_index(op.f("ix_reply_sessions_id"), "reply_sessions", ["id"], unique=False)
    op.create_index(op.f("ix_reply_sessions_reply_id"), "reply_sessions", ["reply_id"], unique=False)
    op.create_index(op.f("ix_reply_sessions_session_id"), "reply_sessions", ["session_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_reply_sessions_session_id"), table_name="reply_sessions")
    op.drop_index(op.f("ix_reply_sessions_reply_id"), table_name="reply_sessions")
    op.drop_index(op.f("ix_reply_sessions_id"), table_name="reply_sessions")
    op.drop_table("reply_sessions")
