"""add datetime fields to entry

Revision ID: ff36817a6c4c
Revises: 7e4e9ee0ea62
Create Date: 2025-09-17 23:04:32.341887

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "ff36817a6c4c"
down_revision: Union[str, None] = "7e4e9ee0ea62"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "entries", sa.Column("source_created_at", sa.DateTime(), nullable=True)
    )
    op.add_column(
        "entries", sa.Column("source_updated_at", sa.DateTime(), nullable=True)
    )
    op.add_column(
        "entry_updates", sa.Column("source_created_at", sa.DateTime(), nullable=True)
    )
    op.add_column(
        "entry_updates", sa.Column("source_updated_at", sa.DateTime(), nullable=True)
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("entries", "source_created_at")
    op.drop_column("entries", "source_updated_at")
    op.drop_column("entry_updates", "source_created_at")
    op.drop_column("entry_updates", "source_updated_at")
