"""drop hermes tracking tables

Revision ID: 20260904_0011
Revises: 20260904_0010
Create Date: 2026-09-04 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20260904_0011"
down_revision: Union[str, None] = "20260904_0010"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_table("hermess_messages")
    op.drop_index(op.f("ix_hermes_sessions_session_id"), table_name="hermes_sessions")
    op.drop_table("hermes_sessions")
    op.drop_index(op.f("ix_reply_sessions_session_id"), table_name="reply_sessions")
    op.drop_index(op.f("ix_reply_sessions_reply_id"), table_name="reply_sessions")
    op.drop_index(op.f("ix_reply_sessions_id"), table_name="reply_sessions")
    op.drop_table("reply_sessions")
    op.drop_index(op.f("ix_message_sessions_session_id"), table_name="message_sessions")
    op.drop_index(op.f("ix_message_sessions_message_id"), table_name="message_sessions")
    op.drop_index(op.f("ix_message_sessions_id"), table_name="message_sessions")
    op.drop_table("message_sessions")


def downgrade() -> None:
    op.create_table(
        "message_sessions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("message_id", sa.Integer(), nullable=False),
        sa.Column("session_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["message_id"], ["message_logs.id"]),
        sa.ForeignKeyConstraint(["session_id"], ["sessions.session_id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_message_sessions_id"), "message_sessions", ["id"], unique=False)
    op.create_index(op.f("ix_message_sessions_message_id"), "message_sessions", ["message_id"], unique=False)
    op.create_index(op.f("ix_message_sessions_session_id"), "message_sessions", ["session_id"], unique=False)

    op.create_table(
        "reply_sessions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("reply_id", sa.Integer(), nullable=False),
        sa.Column("session_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["reply_id"], ["bot_replies.id"]),
        sa.ForeignKeyConstraint(["session_id"], ["sessions.session_id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_reply_sessions_id"), "reply_sessions", ["id"], unique=False)
    op.create_index(op.f("ix_reply_sessions_reply_id"), "reply_sessions", ["reply_id"], unique=False)
    op.create_index(op.f("ix_reply_sessions_session_id"), "reply_sessions", ["session_id"], unique=False)

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
