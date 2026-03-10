"""add biometric_license_count to business

Revision ID: add_biometric_license_count
Revises: 
Create Date: 2026-02-14

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_biometric_license_count'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Add biometric_license_count column to businesses table
    op.add_column('businesses', sa.Column('biometric_license_count', sa.Integer(), nullable=False, server_default='3'))


def downgrade():
    # Remove biometric_license_count column from businesses table
    op.drop_column('businesses', 'biometric_license_count')
