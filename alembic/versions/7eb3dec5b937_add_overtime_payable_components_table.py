"""add_overtime_payable_components_table

Revision ID: 7eb3dec5b937
Revises: add_user_address_fields
Create Date: 2026-01-14 16:07:27.876607

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7eb3dec5b937'
down_revision: Union[str, None] = 'add_user_address_fields'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create overtime_policy_payable_components table
    op.create_table(
        'overtime_policy_payable_components',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('business_id', sa.Integer(), nullable=False),
        sa.Column('policy_id', sa.Integer(), nullable=False),
        sa.Column('component_id', sa.Integer(), nullable=False),
        sa.Column('is_payable', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['business_id'], ['businesses.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['policy_id'], ['overtime_policies.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['component_id'], ['salary_components.id'], ondelete='CASCADE'),
    )
    
    # Create indexes
    op.create_index('ix_overtime_policy_payable_components_business_id', 'overtime_policy_payable_components', ['business_id'])
    op.create_index('ix_overtime_policy_payable_components_policy_id', 'overtime_policy_payable_components', ['policy_id'])
    op.create_index('ix_overtime_policy_payable_components_component_id', 'overtime_policy_payable_components', ['component_id'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_overtime_policy_payable_components_component_id', table_name='overtime_policy_payable_components')
    op.drop_index('ix_overtime_policy_payable_components_policy_id', table_name='overtime_policy_payable_components')
    op.drop_index('ix_overtime_policy_payable_components_business_id', table_name='overtime_policy_payable_components')
    
    # Drop table
    op.drop_table('overtime_policy_payable_components')
