"""add name to gazzetes

Revision ID: 68b525d19bc0
Revises: ff36817a6c4c
Create Date: 2025-09-18 10:11:46.218777

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "68b525d19bc0"
down_revision: Union[str, None] = "ff36817a6c4c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("gazettes", sa.Column("name", sa.String(), nullable=True))

    op.execute(sa.text("UPDATE gazettes SET name = 'Gazette'"))

    op.alter_column("gazettes", "name", nullable=False)

    op.add_column("sections", sa.Column("name", sa.String(), nullable=True))

    op.execute(sa.text("UPDATE sections SET name = 'Section'"))

    op.alter_column("sections", "name", nullable=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("gazettes", "name")
    op.drop_column("sections", "name")
