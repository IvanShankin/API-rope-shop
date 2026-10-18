"""add_quote_request_number_seq

Revision ID: 70d03b16d3e5
Revises: 0ca54d2aff7f
Create Date: 2026-10-17 01:29:01.407355

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '70d03b16d3e5'
down_revision: Union[str, Sequence[str], None] = '0ca54d2aff7f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("CREATE SEQUENCE IF NOT EXISTS quote_request_number_seq START 1;")
    op.execute(
        """
        SELECT setval(
            'quote_request_number_seq',
            COALESCE((SELECT COUNT(*) FROM quote_requests), 0) + 1,
            false
        );
        """
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DROP SEQUENCE IF EXISTS quote_request_number_seq;")
