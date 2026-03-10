"""add contact inquiry table

Revision ID: add_contact_inquiry
Revises: 
Create Date: 2024-01-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_contact_inquiry'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Create contact_inquiries table
    op.create_table(
        'contact_inquiries',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('phone', sa.String(length=50), nullable=True),
        sa.Column('company_name', sa.String(length=255), nullable=False),
        sa.Column('number_of_employees', sa.String(length=50), nullable=False),
        sa.Column('industry', sa.String(length=100), nullable=True),
        sa.Column('message', sa.Text(), nullable=True),
        sa.Column('source', sa.Enum('landing_page', 'contact_form', 'demo_request', 'phone', 'email', 'referral', name='inquirysource', native_enum=False), nullable=False),
        sa.Column('status', sa.Enum('new', 'contacted', 'qualified', 'converted', 'closed', 'spam', name='inquirystatus', native_enum=False), nullable=False),
        sa.Column('assigned_to_id', sa.Integer(), nullable=True),
        sa.Column('ip_address', sa.String(length=50), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('referrer_url', sa.String(length=500), nullable=True),
        sa.Column('contacted_at', sa.DateTime(), nullable=True),
        sa.Column('follow_up_date', sa.DateTime(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('is_spam', sa.Boolean(), nullable=True, default=False),
        sa.Column('is_priority', sa.Boolean(), nullable=True, default=False),
        sa.Column('email_sent', sa.Boolean(), nullable=True, default=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index(op.f('ix_contact_inquiries_id'), 'contact_inquiries', ['id'], unique=False)
    op.create_index(op.f('ix_contact_inquiries_full_name'), 'contact_inquiries', ['full_name'], unique=False)
    op.create_index(op.f('ix_contact_inquiries_email'), 'contact_inquiries', ['email'], unique=False)
    op.create_index(op.f('ix_contact_inquiries_company_name'), 'contact_inquiries', ['company_name'], unique=False)


def downgrade():
    # Drop indexes
    op.drop_index(op.f('ix_contact_inquiries_company_name'), table_name='contact_inquiries')
    op.drop_index(op.f('ix_contact_inquiries_email'), table_name='contact_inquiries')
    op.drop_index(op.f('ix_contact_inquiries_full_name'), table_name='contact_inquiries')
    op.drop_index(op.f('ix_contact_inquiries_id'), table_name='contact_inquiries')
    
    # Drop table
    op.drop_table('contact_inquiries')
