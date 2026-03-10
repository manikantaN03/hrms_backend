"""make mobile field optional

Revision ID: make_mobile_optional
Revises: 
Create Date: 2026-02-25 12:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'make_mobile_optional'
down_revision = None  # Set this to the latest migration ID
branch_labels = None
depends_on = None


def upgrade():
    # Make mobile field nullable
    op.alter_column('employees', 'mobile',
               existing_type=sa.String(length=20),
               nullable=True)


def downgrade():
    # Make mobile field required again
    op.alter_column('employees', 'mobile',
               existing_type=sa.String(length=20),
               nullable=False)
