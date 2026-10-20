"""storefront product fields (slug, old price, rating, badge, sizes)

Revision ID: 3b7e1c2d9a41
Revises: 906ac174f87c
Create Date: 2026-10-20 23:45:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3b7e1c2d9a41'
down_revision = '906ac174f87c'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('products', sa.Column('slug', sa.String(length=120), nullable=True))
    op.add_column('products', sa.Column('old_price', sa.Numeric(precision=10, scale=2), nullable=True))
    op.add_column('products', sa.Column('rating', sa.Float(), nullable=True))
    op.add_column('products', sa.Column('badge', sa.String(length=40), nullable=True))
    op.add_column('products', sa.Column('sizes', sa.JSON(), nullable=True))
    op.create_index('ix_products_slug', 'products', ['slug'], unique=True)


def downgrade():
    with op.batch_alter_table('products') as batch_op:
        batch_op.drop_index('ix_products_slug')
        batch_op.drop_column('sizes')
        batch_op.drop_column('badge')
        batch_op.drop_column('rating')
        batch_op.drop_column('old_price')
        batch_op.drop_column('slug')
