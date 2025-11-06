"""Add last_entry_updated_at

Revision ID: 53d7ecfa2a78
Revises: 1320e894ea22
Create Date: 2025-11-06 08:58:38.753724

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "53d7ecfa2a78"
down_revision: Union[str, None] = "1320e894ea22"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "entries", sa.Column("last_update_created_at", sa.DateTime(), nullable=True)
    )
    op.execute(
        sa.text(
            "UPDATE entries SET last_update_created_at = (SELECT MAX(source_created_at) FROM entry_updates WHERE entry_id = entries.id)"
        )
    )
    op.alter_column("entries", "last_update_created_at", nullable=True)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("entries", "last_update_created_at")
