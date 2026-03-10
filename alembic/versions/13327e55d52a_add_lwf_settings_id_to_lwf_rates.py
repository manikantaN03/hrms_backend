"""add_lwf_settings_id_to_lwf_rates

Revision ID: 13327e55d52a
Revises: 7eb3dec5b937
Create Date: 2026-01-14 23:47:47.848974

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '13327e55d52a'
down_revision: Union[str, None] = '7eb3dec5b937'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create lwf_settings table if it doesn't exist
    op.create_table(
        'lwf_settings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('business_id', sa.Integer(), nullable=False),
        sa.Column('is_enabled', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['business_id'], ['businesses.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('business_id')
    )
    op.create_index(op.f('ix_lwf_settings_business_id'), 'lwf_settings', ['business_id'], unique=False)
    
    # Add lwf_settings_id column to lwf_rates table if it doesn't exist
    # First check if the column exists
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('lwf_rates')]
    
    if 'lwf_settings_id' not in columns:
        # Add the column as nullable first
        op.add_column('lwf_rates', sa.Column('lwf_settings_id', sa.Integer(), nullable=True))
        
        # Create lwf_settings records for each business that has lwf_rates
        conn.execute(sa.text("""
            INSERT INTO lwf_settings (business_id, is_enabled, created_at, updated_at)
            SELECT DISTINCT business_id, false, NOW(), NOW()
            FROM lwf_rates
            WHERE business_id NOT IN (SELECT business_id FROM lwf_settings)
        """))
        
        # Update lwf_rates to link to lwf_settings
        conn.execute(sa.text("""
            UPDATE lwf_rates
            SET lwf_settings_id = (
                SELECT id FROM lwf_settings WHERE lwf_settings.business_id = lwf_rates.business_id
            )
        """))
        
        # Now make the column non-nullable
        op.alter_column('lwf_rates', 'lwf_settings_id', nullable=False)
        
        # Add foreign key constraint
        op.create_foreign_key('fk_lwf_rates_lwf_settings_id', 'lwf_rates', 'lwf_settings', ['lwf_settings_id'], ['id'])
        
        # Add index
        op.create_index(op.f('ix_lwf_rates_lwf_settings_id'), 'lwf_rates', ['lwf_settings_id'], unique=False)


def downgrade() -> None:
    # Remove the foreign key and column
    op.drop_index(op.f('ix_lwf_rates_lwf_settings_id'), table_name='lwf_rates')
    op.drop_constraint('fk_lwf_rates_lwf_settings_id', 'lwf_rates', type_='foreignkey')
    op.drop_column('lwf_rates', 'lwf_settings_id')
    
    # Drop lwf_settings table
    op.drop_index(op.f('ix_lwf_settings_business_id'), table_name='lwf_settings')
    op.drop_table('lwf_settings')
