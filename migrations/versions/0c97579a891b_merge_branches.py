"""merge branches

Revision ID: 0c97579a891b
Revises: add_location_to_store, f40d4d1a7f40
Create Date: 2025-05-07 14:51:04.921184

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0c97579a891b'
down_revision = ('add_location_to_store', 'f40d4d1a7f40')
branch_labels = None
depends_on = None

# This file should be checked for existence first

def upgrade():
    pass


def downgrade():
    pass
