"""add_gazettes_table

Revision ID: 76664a00f5b8
Revises: f7755a0c649b
Create Date: 2025-09-16 23:15:57.294206

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "76664a00f5b8"
down_revision: Union[str, None] = "f7755a0c649b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create gazettes table
    op.create_table(
        "gazettes",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("header", sa.String(), nullable=False),
        sa.Column("subheader", sa.String(), nullable=True),
        sa.Column("theme", sa.String(), nullable=True),
        sa.Column("tags", postgresql.ARRAY(sa.String()), default=[], nullable=False),
        sa.Column("labels", postgresql.JSONB(), default={}, nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("share_key", sa.String(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")
        ),
        sa.Column(
            "updated_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")
        ),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("share_key", name="uq_gazettes_share_key"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Drop gazettes table
    op.drop_table("gazettes")
