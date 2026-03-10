"""Add business_id to CRM tables

Revision ID: add_business_id_crm
Revises: d3e923ab9f67
Create Date: 2026-03-06 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_business_id_crm'
down_revision: Union[str, None] = 'd3e923ab9f67'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add business_id column to crm_companies
    op.add_column('crm_companies', sa.Column('business_id', sa.Integer(), nullable=True))
    op.create_index(op.f('ix_crm_companies_business_id'), 'crm_companies', ['business_id'], unique=False)
    op.create_foreign_key('fk_crm_companies_business_id', 'crm_companies', 'businesses', ['business_id'], ['id'])
    
    # Add business_id column to crm_contacts
    op.add_column('crm_contacts', sa.Column('business_id', sa.Integer(), nullable=True))
    op.create_index(op.f('ix_crm_contacts_business_id'), 'crm_contacts', ['business_id'], unique=False)
    op.create_foreign_key('fk_crm_contacts_business_id', 'crm_contacts', 'businesses', ['business_id'], ['id'])
    
    # Add business_id column to crm_deals
    op.add_column('crm_deals', sa.Column('business_id', sa.Integer(), nullable=True))
    op.create_index(op.f('ix_crm_deals_business_id'), 'crm_deals', ['business_id'], unique=False)
    op.create_foreign_key('fk_crm_deals_business_id', 'crm_deals', 'businesses', ['business_id'], ['id'])
    
    # Add business_id column to crm_activities
    op.add_column('crm_activities', sa.Column('business_id', sa.Integer(), nullable=True))
    op.create_index(op.f('ix_crm_activities_business_id'), 'crm_activities', ['business_id'], unique=False)
    op.create_foreign_key('fk_crm_activities_business_id', 'crm_activities', 'businesses', ['business_id'], ['id'])
    
    # Add business_id column to crm_pipelines
    op.add_column('crm_pipelines', sa.Column('business_id', sa.Integer(), nullable=True))
    op.create_index(op.f('ix_crm_pipelines_business_id'), 'crm_pipelines', ['business_id'], unique=False)
    op.create_foreign_key('fk_crm_pipelines_business_id', 'crm_pipelines', 'businesses', ['business_id'], ['id'])
    
    # Update existing records to set business_id = 1 (default business)
    # This is a safe default for existing data
    op.execute("UPDATE crm_companies SET business_id = 1 WHERE business_id IS NULL")
    op.execute("UPDATE crm_contacts SET business_id = 1 WHERE business_id IS NULL")
    op.execute("UPDATE crm_deals SET business_id = 1 WHERE business_id IS NULL")
    op.execute("UPDATE crm_activities SET business_id = 1 WHERE business_id IS NULL")
    op.execute("UPDATE crm_pipelines SET business_id = 1 WHERE business_id IS NULL")
    
    # Make business_id NOT NULL after setting defaults
    op.alter_column('crm_companies', 'business_id', nullable=False)
    op.alter_column('crm_contacts', 'business_id', nullable=False)
    op.alter_column('crm_deals', 'business_id', nullable=False)
    op.alter_column('crm_activities', 'business_id', nullable=False)
    op.alter_column('crm_pipelines', 'business_id', nullable=False)


def downgrade() -> None:
    # Remove business_id columns and constraints
    op.drop_constraint('fk_crm_pipelines_business_id', 'crm_pipelines', type_='foreignkey')
    op.drop_index(op.f('ix_crm_pipelines_business_id'), table_name='crm_pipelines')
    op.drop_column('crm_pipelines', 'business_id')
    
    op.drop_constraint('fk_crm_activities_business_id', 'crm_activities', type_='foreignkey')
    op.drop_index(op.f('ix_crm_activities_business_id'), table_name='crm_activities')
    op.drop_column('crm_activities', 'business_id')
    
    op.drop_constraint('fk_crm_deals_business_id', 'crm_deals', type_='foreignkey')
    op.drop_index(op.f('ix_crm_deals_business_id'), table_name='crm_deals')
    op.drop_column('crm_deals', 'business_id')
    
    op.drop_constraint('fk_crm_contacts_business_id', 'crm_contacts', type_='foreignkey')
    op.drop_index(op.f('ix_crm_contacts_business_id'), table_name='crm_contacts')
    op.drop_column('crm_contacts', 'business_id')
    
    op.drop_constraint('fk_crm_companies_business_id', 'crm_companies', type_='foreignkey')
    op.drop_index(op.f('ix_crm_companies_business_id'), table_name='crm_companies')
    op.drop_column('crm_companies', 'business_id')
