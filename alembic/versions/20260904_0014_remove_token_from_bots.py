"""remove token column from bots

Revision ID: 20260904_0014
Revises: 20260904_0013
Create Date: 2026-09-04 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20260904_0014"
down_revision: Union[str, None] = "20260904_0013"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("bots", schema=None) as batch_op:
        batch_op.drop_column("token")


def downgrade() -> None:
    with op.batch_alter_table("bots", schema=None) as batch_op:
        batch_op.add_column(sa.Column("token", sa.String(length=255), nullable=False, server_default=""))
        batch_op.create_unique_constraint("uq_bots_token", ["token"])
