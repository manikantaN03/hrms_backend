"""add remote sessions table

Revision ID: add_remote_sessions
Revises: 
Create Date: 2026-02-14

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_remote_sessions'
down_revision = None  # Set this to the latest migration ID
branch_labels = None
depends_on = None


def upgrade():
    # Create enum types
    op.execute("""
        CREATE TYPE remotesessionstatus AS ENUM (
            'pending', 'scheduled', 'in_progress', 'completed', 'cancelled'
        )
    """)
    
    op.execute("""
        CREATE TYPE remotesessiontype AS ENUM (
            'technical_support', 'software_installation', 'troubleshooting',
            'training', 'system_maintenance', 'other'
        )
    """)
    
    # Create remote_sessions table
    op.create_table(
        'remote_sessions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('business_id', sa.Integer(), nullable=False),
        sa.Column('employee_id', sa.Integer(), nullable=False),
        sa.Column('support_agent_id', sa.Integer(), nullable=True),
        sa.Column('session_type', postgresql.ENUM(name='remotesessiontype'), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('status', postgresql.ENUM(name='remotesessionstatus'), nullable=False),
        sa.Column('requested_date', sa.DateTime(), nullable=False),
        sa.Column('scheduled_date', sa.DateTime(), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('computer_name', sa.String(length=100), nullable=True),
        sa.Column('ip_address', sa.String(length=50), nullable=True),
        sa.Column('operating_system', sa.String(length=100), nullable=True),
        sa.Column('issue_category', sa.String(length=100), nullable=True),
        sa.Column('agent_notes', sa.Text(), nullable=True),
        sa.Column('resolution_notes', sa.Text(), nullable=True),
        sa.Column('rating', sa.Integer(), nullable=True),
        sa.Column('feedback', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('updated_by', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['business_id'], ['businesses.id'], ),
        sa.ForeignKeyConstraint(['employee_id'], ['employees.id'], ),
        sa.ForeignKeyConstraint(['support_agent_id'], ['employees.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index('ix_remote_sessions_business_id', 'remote_sessions', ['business_id'])
    op.create_index('ix_remote_sessions_employee_id', 'remote_sessions', ['employee_id'])
    op.create_index('ix_remote_sessions_support_agent_id', 'remote_sessions', ['support_agent_id'])
    op.create_index('ix_remote_sessions_status', 'remote_sessions', ['status'])


def downgrade():
    # Drop indexes
    op.drop_index('ix_remote_sessions_status', table_name='remote_sessions')
    op.drop_index('ix_remote_sessions_support_agent_id', table_name='remote_sessions')
    op.drop_index('ix_remote_sessions_employee_id', table_name='remote_sessions')
    op.drop_index('ix_remote_sessions_business_id', table_name='remote_sessions')
    
    # Drop table
    op.drop_table('remote_sessions')
    
    # Drop enum types
    op.execute('DROP TYPE remotesessiontype')
    op.execute('DROP TYPE remotesessionstatus')
