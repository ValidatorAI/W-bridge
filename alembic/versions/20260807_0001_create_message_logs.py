"""create message logs table

Revision ID: 20260807_0001
Revises:
Create Date: 2026-08-07 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "20260807_0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "message_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_name", sa.String(length=255), nullable=False),
        sa.Column("room_path", sa.String(length=500), nullable=False),
        sa.Column("raw_html", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_message_logs_id"), "message_logs", ["id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_message_logs_id"), table_name="message_logs")
    op.drop_table("message_logs")
