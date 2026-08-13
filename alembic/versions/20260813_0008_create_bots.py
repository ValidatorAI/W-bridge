"""create bots

Revision ID: 20260813_0008
Revises: 20260812_0007
Create Date: 2026-08-13 00:20:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "20260813_0008"
down_revision: Union[str, None] = "20260812_0007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "bots",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("profile_name", sa.String(length=255), nullable=False, server_default="default"),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("token", sa.String(length=255), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token"),
    )
    op.create_index(op.f("ix_bots_id"), "bots", ["id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_bots_id"), table_name="bots")
    op.drop_table("bots")
