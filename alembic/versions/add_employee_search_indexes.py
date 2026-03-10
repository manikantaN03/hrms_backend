"""add employee search indexes

Revision ID: add_search_indexes_001
Revises: d3e923ab9f67
Create Date: 2024-02-28 12:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_search_indexes_001'
down_revision: Union[str, None] = 'd3e923ab9f67'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    """Add indexes for faster employee search"""
    
    # Add index on first_name for faster ILIKE searches
    op.create_index(
        'idx_employees_first_name',
        'employees',
        ['first_name'],
        postgresql_ops={'first_name': 'varchar_pattern_ops'}
    )
    
    # Add index on last_name for faster ILIKE searches
    op.create_index(
        'idx_employees_last_name',
        'employees',
        ['last_name'],
        postgresql_ops={'last_name': 'varchar_pattern_ops'}
    )
    
    # Add index on employee_code for faster ILIKE searches
    op.create_index(
        'idx_employees_employee_code',
        'employees',
        ['employee_code'],
        postgresql_ops={'employee_code': 'varchar_pattern_ops'}
    )
    
    # Add composite index on employee_status for faster filtering
    op.create_index(
        'idx_employees_status',
        'employees',
        ['employee_status']
    )
    
    # Add composite index on business_id and employee_status
    op.create_index(
        'idx_employees_business_status',
        'employees',
        ['business_id', 'employee_status']
    )


def downgrade():
    """Remove indexes"""
    op.drop_index('idx_employees_business_status', table_name='employees')
    op.drop_index('idx_employees_status', table_name='employees')
    op.drop_index('idx_employees_employee_code', table_name='employees')
    op.drop_index('idx_employees_last_name', table_name='employees')
    op.drop_index('idx_employees_first_name', table_name='employees')
