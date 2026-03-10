"""Add HR and Indirect Manager fields to employees table

Revision ID: add_manager_fields
Revises: 
Create Date: 2026-01-23 16:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_manager_fields'
down_revision = '13327e55d52a'  # Latest revision ID
branch_labels = None
depends_on = None


def upgrade():
    """Add hr_manager_id and indirect_manager_id columns to employees table"""
    
    # Add the new columns
    op.add_column('employees', sa.Column('hr_manager_id', sa.Integer(), nullable=True))
    op.add_column('employees', sa.Column('indirect_manager_id', sa.Integer(), nullable=True))
    
    # Add foreign key constraints
    op.create_foreign_key(
        'fk_employees_hr_manager_id', 
        'employees', 
        'employees', 
        ['hr_manager_id'], 
        ['id']
    )
    
    op.create_foreign_key(
        'fk_employees_indirect_manager_id', 
        'employees', 
        'employees', 
        ['indirect_manager_id'], 
        ['id']
    )
    
    print("✅ Added hr_manager_id and indirect_manager_id columns to employees table")


def downgrade():
    """Remove hr_manager_id and indirect_manager_id columns from employees table"""
    
    # Drop foreign key constraints first
    op.drop_constraint('fk_employees_hr_manager_id', 'employees', type_='foreignkey')
    op.drop_constraint('fk_employees_indirect_manager_id', 'employees', type_='foreignkey')
    
    # Drop the columns
    op.drop_column('employees', 'hr_manager_id')
    op.drop_column('employees', 'indirect_manager_id')
    
    print("✅ Removed hr_manager_id and indirect_manager_id columns from employees table")