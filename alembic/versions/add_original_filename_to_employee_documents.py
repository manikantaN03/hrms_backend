"""add original_filename to employee_documents

Revision ID: add_original_filename_2026
Revises: d3e923ab9f67
Create Date: 2026-02-17

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_original_filename_2026'
down_revision: Union[str, None] = 'd3e923ab9f67'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # Add original_filename column
    op.add_column('employee_documents', 
        sa.Column('original_filename', sa.String(length=255), nullable=True)
    )
    
    # Migrate existing data: extract original filename from file_path
    # Format: {employee_id}_{uuid}_{original_filename}
    op.execute("""
        UPDATE employee_documents 
        SET original_filename = SUBSTRING(
            file_path, 
            POSITION('_' IN SUBSTRING(file_path, POSITION('_' IN file_path) + 1)) + POSITION('_' IN file_path) + 1
        )
        WHERE original_filename IS NULL AND file_path IS NOT NULL
    """)


def downgrade():
    op.drop_column('employee_documents', 'original_filename')
