"""Add external id to entry updates

Revision ID: 854ec3d91178
Revises: c7bc1e173d5d
Create Date: 2025-09-10 00:23:12.025798

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "854ec3d91178"
down_revision: Union[str, None] = "c7bc1e173d5d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "entry_updates", sa.Column("external_id", sa.String(), nullable=False)
    )
    op.add_column("entry_updates", sa.Column("source_id", sa.UUID(), nullable=False))
    op.create_foreign_key(
        "fk_entry_updates_source_id",
        "entry_updates",
        "sources",
        ["source_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_unique_constraint(
        "uq_entry_updates_external_id", "entry_updates", ["source_id", "external_id"]
    )

    op.create_unique_constraint(
        "uq_entry_updates_external_id_entries", "entries", ["source_id", "external_id"]
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("entry_updates", "external_id")
    op.drop_column("entry_updates", "source_id")
    op.drop_constraint("uq_entry_updates_external_id", "entry_updates")
