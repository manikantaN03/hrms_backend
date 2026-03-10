"""Change profile_image_url to TEXT in crm_contacts

Revision ID: e8f4a9b2c1d3
Revises: d3e923ab9f67
Create Date: 2025-02-14 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e8f4a9b2c1d3'
down_revision: Union[str, None] = 'd3e923ab9f67'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Change profile_image_url column from VARCHAR(255) to TEXT
    to support base64 encoded images which can be very long
    """
    # For PostgreSQL, we can use ALTER COLUMN TYPE
    op.alter_column(
        'crm_contacts',
        'profile_image_url',
        type_=sa.Text(),
        existing_type=sa.String(255),
        existing_nullable=True
    )


def downgrade() -> None:
    """
    Revert profile_image_url column back to VARCHAR(255)
    WARNING: This may truncate data if any profile_image_url values exceed 255 characters
    """
    op.alter_column(
        'crm_contacts',
        'profile_image_url',
        type_=sa.String(255),
        existing_type=sa.Text(),
        existing_nullable=True
    )
