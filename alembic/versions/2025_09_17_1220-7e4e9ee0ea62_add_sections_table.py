"""add_sections_table

Revision ID: 7e4e9ee0ea62
Revises: 76664a00f5b8
Create Date: 2025-09-17 12:20:22.351834

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "7e4e9ee0ea62"
down_revision: Union[str, None] = "76664a00f5b8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create sections table
    op.create_table(
        "sections",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("header", sa.String(), nullable=False),
        sa.Column("subheader", sa.String(), nullable=True),
        sa.Column(
            "tags",
            postgresql.ARRAY(sa.String()),
            nullable=False,
            server_default=sa.text("'{}'::varchar[]"),
        ),
        sa.Column(
            "labels",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("gazette_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_at",
            postgresql.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            postgresql.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("deleted_at", postgresql.TIMESTAMP(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["gazette_id"], ["gazettes.id"], ondelete="CASCADE"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Drop sections table
    op.drop_table("sections")
