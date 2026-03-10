"""Add employee salary units table

Revision ID: add_employee_salary_units
Revises: 
Create Date: 2026-01-28 17:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_employee_salary_units'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Create employee_salary_units table
    op.create_table('employee_salary_units',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('business_id', sa.Integer(), nullable=False),
        sa.Column('employee_id', sa.Integer(), nullable=False),
        sa.Column('unit_name', sa.String(length=255), nullable=False),
        sa.Column('unit_type', sa.String(length=100), nullable=False),
        sa.Column('amount', sa.Numeric(precision=15, scale=2), nullable=False, default=0),
        sa.Column('effective_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=True),
        sa.Column('comments', sa.Text(), nullable=True),
        sa.Column('is_arrear', sa.Boolean(), nullable=True, default=False),
        sa.Column('is_active', sa.Boolean(), nullable=True, default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('updated_by', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['business_id'], ['businesses.id'], ),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['employee_id'], ['employees.id'], ),
        sa.ForeignKeyConstraint(['updated_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_employee_salary_units_id'), 'employee_salary_units', ['id'], unique=False)
    op.create_index('ix_employee_salary_units_employee_date', 'employee_salary_units', ['employee_id', 'effective_date'], unique=False)
    op.create_index('ix_employee_salary_units_business_active', 'employee_salary_units', ['business_id', 'is_active'], unique=False)


def downgrade():
    op.drop_index('ix_employee_salary_units_business_active', table_name='employee_salary_units')
    op.drop_index('ix_employee_salary_units_employee_date', table_name='employee_salary_units')
    op.drop_index(op.f('ix_employee_salary_units_id'), table_name='employee_salary_units')
    op.drop_table('employee_salary_units')