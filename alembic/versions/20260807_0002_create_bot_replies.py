"""create bot replies table

Revision ID: 20260807_0002
Revises: 20260807_0001
Create Date: 2026-08-07 00:10:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "20260807_0002"
down_revision: Union[str, None] = "20260807_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "bot_replies",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("message_id", sa.Integer(), nullable=False),
        sa.Column("reply_text", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["message_id"], ["message_logs.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_bot_replies_id"), "bot_replies", ["id"], unique=False)
    op.create_index(op.f("ix_bot_replies_message_id"), "bot_replies", ["message_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_bot_replies_message_id"), table_name="bot_replies")
    op.drop_index(op.f("ix_bot_replies_id"), table_name="bot_replies")
    op.drop_table("bot_replies")
