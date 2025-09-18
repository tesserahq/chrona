"""add raw_boddy to digest

Revision ID: 842e409ddd97
Revises: 68b525d19bc0
Create Date: 2025-09-18 11:24:44.009922

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "842e409ddd97"
down_revision: Union[str, None] = "68b525d19bc0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("digests", sa.Column("raw_body", sa.String(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("digests", "raw_body")
