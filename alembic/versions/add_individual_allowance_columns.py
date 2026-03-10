"""add_individual_allowance_columns_to_employee_salaries

Revision ID: add_individual_allowance_columns
Revises: 13327e55d52a
Create Date: 2026-01-24 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'add_individual_allowance_columns'
down_revision: Union[str, None] = '13327e55d52a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add individual allowance columns to employee_salaries table
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    
    # Check if employee_salaries table exists
    tables = inspector.get_table_names()
    if 'employee_salaries' in tables:
        columns = [col['name'] for col in inspector.get_columns('employee_salaries')]
        
        # Add columns if they don't exist
        if 'house_rent_allowance' not in columns:
            op.add_column('employee_salaries', sa.Column('house_rent_allowance', sa.Numeric(precision=15, scale=2), server_default='0', nullable=True))
        
        if 'special_allowance' not in columns:
            op.add_column('employee_salaries', sa.Column('special_allowance', sa.Numeric(precision=15, scale=2), server_default='0', nullable=True))
        
        if 'medical_allowance' not in columns:
            op.add_column('employee_salaries', sa.Column('medical_allowance', sa.Numeric(precision=15, scale=2), server_default='0', nullable=True))
        
        if 'conveyance_allowance' not in columns:
            op.add_column('employee_salaries', sa.Column('conveyance_allowance', sa.Numeric(precision=15, scale=2), server_default='0', nullable=True))
        
        if 'telephone_allowance' not in columns:
            op.add_column('employee_salaries', sa.Column('telephone_allowance', sa.Numeric(precision=15, scale=2), server_default='0', nullable=True))
        
        # Update existing records with calculated values based on current basic_salary
        conn.execute(sa.text("""
            UPDATE employee_salaries 
            SET 
                house_rent_allowance = COALESCE(house_rent_allowance, basic_salary * 0.4),
                special_allowance = COALESCE(special_allowance, 8000),
                medical_allowance = COALESCE(medical_allowance, 500),
                conveyance_allowance = COALESCE(conveyance_allowance, 400),
                telephone_allowance = COALESCE(telephone_allowance, 500)
            WHERE 
                house_rent_allowance IS NULL OR
                special_allowance IS NULL OR
                medical_allowance IS NULL OR
                conveyance_allowance IS NULL OR
                telephone_allowance IS NULL
        """))


def downgrade() -> None:
    # Remove the added columns
    op.drop_column('employee_salaries', 'telephone_allowance')
    op.drop_column('employee_salaries', 'conveyance_allowance')
    op.drop_column('employee_salaries', 'medical_allowance')
    op.drop_column('employee_salaries', 'special_allowance')
    op.drop_column('employee_salaries', 'house_rent_allowance')