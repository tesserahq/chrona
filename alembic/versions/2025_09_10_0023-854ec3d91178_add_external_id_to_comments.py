"""Add external id to comments

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
    op.add_column("comments", sa.Column("external_id", sa.String(), nullable=False))
    op.add_column("comments", sa.Column("source_id", sa.UUID(), nullable=False))
    op.create_foreign_key(
        "fk_comments_source_id",
        "comments",
        "sources",
        ["source_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("comments", "external_id")
    op.drop_column("comments", "source_id")
