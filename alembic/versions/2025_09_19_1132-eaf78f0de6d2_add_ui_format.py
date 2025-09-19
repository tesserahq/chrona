"""add ui_format

Revision ID: eaf78f0de6d2
Revises: 842e409ddd97
Create Date: 2025-09-19 11:32:59.220998

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "eaf78f0de6d2"
down_revision: Union[str, None] = "842e409ddd97"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "digest_generation_configs",
        sa.Column("ui_format", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )
    op.execute(sa.text("UPDATE digest_generation_configs SET ui_format = '{}'"))
    op.alter_column("digest_generation_configs", "ui_format", nullable=False)

    op.add_column(
        "digests",
        sa.Column("ui_format", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )
    op.execute(sa.text("UPDATE digests SET ui_format = '{}'"))
    op.alter_column("digests", "ui_format", nullable=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("digest_generation_configs", "ui_format")
    op.drop_column("digests", "ui_format")
