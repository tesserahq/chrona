"""Add published date to digests

Revision ID: 1320e894ea22
Revises: 8fd5a9759e76
Create Date: 2025-11-03 11:08:34.910883

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "1320e894ea22"
down_revision: Union[str, None] = "8fd5a9759e76"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("digests", sa.Column("published_at", sa.DateTime(), nullable=True))
    op.execute(
        sa.text(
            "UPDATE digests SET published_at = updated_at WHERE status = 'published'"
        )
    )
    op.alter_column("digests", "published_at", nullable=True)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("digests", "published_at")
