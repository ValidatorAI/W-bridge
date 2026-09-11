"""create mcp call logs

Revision ID: 20260911_0017
Revises: 20260911_0016
Create Date: 2026-09-11 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "20260911_0017"
down_revision: Union[str, None] = "20260911_0016"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "mcp_call_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("jsonrpc_id", sa.String(length=255), nullable=True),
        sa.Column("tool_call_name", sa.String(length=255), nullable=False),
        sa.Column("params_sanitized", sa.JSON(), nullable=True),
        sa.Column("is_error", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("result_preview", sa.Text(), nullable=True),
        sa.Column("result_size", sa.Integer(), nullable=True),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_mcp_call_logs_id"), "mcp_call_logs", ["id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_mcp_call_logs_id"), table_name="mcp_call_logs")
    op.drop_table("mcp_call_logs")
