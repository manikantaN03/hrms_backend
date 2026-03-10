"""Add address fields to user model

Revision ID: add_user_address_fields
Revises: d3e923ab9f67
Create Date: 2026-01-02 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_user_address_fields'
down_revision = 'd3e923ab9f67'
branch_labels = None
depends_on = None


def upgrade():
    """Add address fields to users table"""
    # Add phone field
    op.add_column('users', sa.Column('phone', sa.String(length=20), nullable=True))
    
    # Add address fields
    op.add_column('users', sa.Column('country', sa.String(length=100), nullable=True))
    op.add_column('users', sa.Column('state', sa.String(length=100), nullable=True))
    op.add_column('users', sa.Column('city', sa.String(length=100), nullable=True))
    op.add_column('users', sa.Column('postal_code', sa.String(length=20), nullable=True))


def downgrade():
    """Remove address fields from users table"""
    op.drop_column('users', 'postal_code')
    op.drop_column('users', 'city')
    op.drop_column('users', 'state')
    op.drop_column('users', 'country')
    op.drop_column('users', 'phone')