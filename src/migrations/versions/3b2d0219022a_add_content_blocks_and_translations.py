"""add_content_blocks_and_translations

Revision ID: 3b2d0219022a
Revises: d2e3de57e8ac
Create Date: 2026-10-18 11:45:08.935725

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3b2d0219022a'
down_revision: Union[str, Sequence[str], None] = 'd2e3de57e8ac'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'content_blocks',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('page_code', sa.String(length=100), nullable=False),
        sa.Column('block_code', sa.String(length=100), nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_content_blocks_block_code'), 'content_blocks', ['block_code'], unique=True)
    op.create_index(op.f('ix_content_blocks_page_code'), 'content_blocks', ['page_code'], unique=False)
    op.create_table(
        'content_block_translations',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('content_block_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=500), nullable=True),
        sa.Column('content', sa.Text(), nullable=True),
        sa.Column('locale', sa.Enum('ru', 'en', 'de', 'rus', 'eng', 'ger', name='locale', native_enum=False, length=10), nullable=False),
        sa.ForeignKeyConstraint(['content_block_id'], ['content_blocks.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('content_block_id', 'locale', name='uq_content_block_id_locale'),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('content_block_translations')
    op.drop_index(op.f('ix_content_blocks_page_code'), table_name='content_blocks')
    op.drop_index(op.f('ix_content_blocks_block_code'), table_name='content_blocks')
    op.drop_table('content_blocks')
