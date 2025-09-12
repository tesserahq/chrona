"""Add state to digests

Revision ID: d9628a3c8137
Revises: 2e55e0b0d561
Create Date: 2025-09-12 09:13:08.956181

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from app.constants.digest_constants import DigestStatuses


# revision identifiers, used by Alembic.
revision: str = "d9628a3c8137"
down_revision: Union[str, None] = "2e55e0b0d561"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add the status column first
    op.add_column("digests", sa.Column("status", sa.String(), nullable=True))

    # Then update existing records to have the default status
    op.execute(sa.text(f"UPDATE digests SET status = '{DigestStatuses.PUBLISHED}'"))

    # Finally make the column non-nullable
    op.alter_column("digests", "status", nullable=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("digests", "status")
