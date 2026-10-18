"""add_reviews_and_review_translations

Revision ID: d2e3de57e8ac
Revises: 4db93845d8fc
Create Date: 2026-10-17 18:04:03.486334

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd2e3de57e8ac'
down_revision: Union[str, Sequence[str], None] = '4db93845d8fc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'reviews',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('author_name', sa.String(length=255), nullable=False),
        sa.Column('rating', sa.SmallInteger(), nullable=True),
        sa.Column('is_published', sa.Boolean(), server_default='false', nullable=False),
        sa.Column(
            'status',
            sa.Enum('new', 'rejected', 'confirmed', name='review_status', native_enum=False, length=20),
            server_default='new',
            nullable=False,
        ),
        sa.Column('index', sa.Integer(), server_default='0', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_table(
        'review_translations',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('review_id', sa.Integer(), nullable=False),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column(
            'locale',
            sa.Enum('ru', 'en', 'de', 'rus', 'eng', 'ger', name='locale', native_enum=False, length=10),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(['review_id'], ['reviews.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('review_id', 'locale', name='uq_review_id_locale'),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('review_translations')
    op.drop_table('reviews')
