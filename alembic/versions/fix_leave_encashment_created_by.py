"""Fix leave encashment created_by foreign key

Revision ID: fix_leave_encashment_created_by
Revises: 
Create Date: 2026-01-17 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'fix_leave_encashment_created_by'
down_revision = None  # Update this with the latest revision ID
branch_labels = None
depends_on = None


def upgrade():
    """Update leave_encashments.created_by to reference users.id instead of employees.id"""
    
    # Drop the existing foreign key constraint
    with op.batch_alter_table('leave_encashments') as batch_op:
        # Drop the foreign key constraint (name may vary by database)
        try:
            batch_op.drop_constraint('fk_leave_encashments_created_by_employees', type_='foreignkey')
        except:
            # If the constraint name is different, try a generic approach
            pass
    
    # Add the new foreign key constraint to users table
    with op.batch_alter_table('leave_encashments') as batch_op:
        batch_op.create_foreign_key(
            'fk_leave_encashments_created_by_users',
            'users',
            ['created_by'],
            ['id']
        )


def downgrade():
    """Revert leave_encashments.created_by to reference employees.id"""
    
    # Drop the foreign key constraint to users
    with op.batch_alter_table('leave_encashments') as batch_op:
        batch_op.drop_constraint('fk_leave_encashments_created_by_users', type_='foreignkey')
    
    # Add back the foreign key constraint to employees table
    with op.batch_alter_table('leave_encashments') as batch_op:
        batch_op.create_foreign_key(
            'fk_leave_encashments_created_by_employees',
            'employees',
            ['created_by'],
            ['id']
        )