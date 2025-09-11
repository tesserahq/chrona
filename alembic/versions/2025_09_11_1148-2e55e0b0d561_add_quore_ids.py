"""add_quore_ids

Revision ID: 2e55e0b0d561
Revises: 854ec3d91178
Create Date: 2025-09-11 11:48:14.094984

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "2e55e0b0d561"
down_revision: Union[str, None] = "854ec3d91178"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "workspaces", sa.Column("quore_workspace_id", sa.String(), nullable=True)
    )
    op.add_column("projects", sa.Column("quore_project_id", sa.String(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("workspaces", "quore_workspace_id")
    op.drop_column("projects", "quore_project_id")
