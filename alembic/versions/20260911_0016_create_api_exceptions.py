"""create api exceptions

Revision ID: 20260911_0016
Revises: 20260905_0015
Create Date: 2026-09-11 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "20260911_0016"
down_revision: Union[str, None] = "20260905_0015"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "api_exceptions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("service_name", sa.String(length=255), nullable=False),
        sa.Column("method", sa.String(length=32), nullable=True),
        sa.Column("endpoint", sa.String(length=2048), nullable=True),
        sa.Column("status_code", sa.Integer(), nullable=True),
        sa.Column("error_type", sa.String(length=255), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=False),
        sa.Column("stored_exception", sa.Text(), nullable=False),
        sa.Column("request_context", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_api_exceptions_id"), "api_exceptions", ["id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_api_exceptions_id"), table_name="api_exceptions")
    op.drop_table("api_exceptions")
