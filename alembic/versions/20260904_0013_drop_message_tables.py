"""drop legacy message tables

Revision ID: 20260904_0013
Revises: 20260904_0012
Create Date: 2026-09-04 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20260904_0013"
down_revision: Union[str, None] = "20260904_0012"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_index(op.f("ix_bot_replies_message_id"), table_name="bot_replies")
    op.drop_index(op.f("ix_bot_replies_id"), table_name="bot_replies")
    op.drop_table("bot_replies")
    op.drop_index(op.f("ix_message_logs_id"), table_name="message_logs")
    op.drop_table("message_logs")


def downgrade() -> None:
    op.create_table(
        "message_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_name", sa.String(length=255), nullable=False),
        sa.Column("room_path", sa.String(length=500), nullable=False),
        sa.Column("raw_html", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_message_logs_id"), "message_logs", ["id"], unique=False)

    op.create_table(
        "bot_replies",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("message_id", sa.Integer(), nullable=False),
        sa.Column("reply_text", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["message_id"], ["message_logs.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_bot_replies_id"), "bot_replies", ["id"], unique=False)
    op.create_index(op.f("ix_bot_replies_message_id"), "bot_replies", ["message_id"], unique=False)
