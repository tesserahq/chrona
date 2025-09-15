"""add_source_assignee_id_to_entries

Revision ID: f7755a0c649b
Revises: d9628a3c8137
Create Date: 2025-09-15 23:39:20.910587

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "f7755a0c649b"
down_revision: Union[str, None] = "d9628a3c8137"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    op.add_column("entries", sa.Column("source_assignee_id", sa.UUID(), nullable=True))
    op.create_foreign_key(
        "fk_entries_source_assignee_id",
        "entries",
        "source_authors",
        ["source_assignee_id"],
        ["id"],
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint("fk_entries_source_assignee_id", "entries", type_="foreignkey")
    op.drop_column("entries", "source_assignee_id")
