"""Add location column to stores table

Revision ID: add_location_to_store
Revises: 
Create Date: 2025-05-07 15:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_location_to_store'
down_revision = None  # Set to None as we don't know the previous revision
branch_labels = None
depends_on = None

def upgrade():
    # Add location column to stores table
    op.add_column('stores', sa.Column('location', sa.String(length=255), nullable=True))

def downgrade():
    # Remove location column from stores table
    op.drop_column('stores', 'location') 