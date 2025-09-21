"""Add query to digest configs

Revision ID: 8fd5a9759e76
Revises: eaf78f0de6d2
Create Date: 2025-09-21 09:08:41.775270

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "8fd5a9759e76"
down_revision: Union[str, None] = "eaf78f0de6d2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "digest_generation_configs", sa.Column("query", sa.String(), nullable=True)
    )
    op.execute(
        sa.text(
            "UPDATE digest_generation_configs SET query = 'Summarize the tasks and their latest updates.'"
        )
    )
    op.alter_column("digest_generation_configs", "query", nullable=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("digest_generation_configs", "query")
