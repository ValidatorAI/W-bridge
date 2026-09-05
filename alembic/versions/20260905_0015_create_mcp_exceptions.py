"""create mcp exceptions

Revision ID: 20260905_0015
Revises: 20260904_0014
Create Date: 2026-09-05 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "20260905_0015"
down_revision: Union[str, None] = "20260904_0014"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "mcp_exceptions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tool_call_name", sa.String(length=255), nullable=False),
        sa.Column("exception", sa.Text(), nullable=False),
        sa.Column("stored_exception", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_mcp_exceptions_id"), "mcp_exceptions", ["id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_mcp_exceptions_id"), table_name="mcp_exceptions")
    op.drop_table("mcp_exceptions")
