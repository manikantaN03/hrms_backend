"""add ncp days to salary reports

Revision ID: add_ncp_days_fields
Revises: 
Create Date: 2026-02-12

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_ncp_days_fields'
down_revision = None  # Set this to the latest migration ID
branch_labels = None
depends_on = None


def upgrade():
    # Add ncp_days and working_days columns to salary_reports table
    op.add_column('salary_reports', sa.Column('ncp_days', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('salary_reports', sa.Column('working_days', sa.Integer(), nullable=False, server_default='30'))


def downgrade():
    # Remove ncp_days and working_days columns
    op.drop_column('salary_reports', 'working_days')
    op.drop_column('salary_reports', 'ncp_days')
