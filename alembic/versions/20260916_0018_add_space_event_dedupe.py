"""add space event dedupe key and dispatch group claim table

Revision ID: 20260916_0018
Revises: 20260911_0017
Create Date: 2026-09-16 00:00:00.000000

Transport-level dedupe for W-space events (one Rails message = one bridge dispatch).

* ``space_events.dedupe_key`` - explicit dedupe key of the routing unit this event
  belongs to. NULL for event families that are not collapsed (see bus/dedupe.py).
* ``space_event_dispatch_groups`` - one row per dedupe key; the UNIQUE index on
  ``dedupe_key`` is the atomic claim that lets exactly one member of a Rails event
  group become the dispatch, while the other members are recorded as duplicates.

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "20260916_0018"
down_revision: Union[str, None] = "20260911_0017"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("space_events", sa.Column("dedupe_key", sa.String(length=512), nullable=True))
    op.create_index("ix_space_events_dedupe_key", "space_events", ["dedupe_key"], unique=False)

    op.create_table(
        "space_event_dispatch_groups",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("dedupe_key", sa.String(length=512), nullable=False),
        sa.Column("lead_space_event_id", sa.String(length=255), nullable=True),
        sa.Column("lead_space_event_row_id", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(length=32), server_default=sa.text("'pending'"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("dispatched_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("result", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_space_event_dispatch_groups_id", "space_event_dispatch_groups", ["id"], unique=False)
    op.create_index(
        "ix_space_event_dispatch_groups_dedupe_key",
        "space_event_dispatch_groups",
        ["dedupe_key"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ix_space_event_dispatch_groups_dedupe_key", table_name="space_event_dispatch_groups")
    op.drop_index("ix_space_event_dispatch_groups_id", table_name="space_event_dispatch_groups")
    op.drop_table("space_event_dispatch_groups")

    op.drop_index("ix_space_events_dedupe_key", table_name="space_events")
    op.drop_column("space_events", "dedupe_key")
