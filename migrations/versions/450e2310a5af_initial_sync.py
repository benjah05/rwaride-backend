"""Bridge for missing revision

Revision ID: 450e2310a5af
Revises: None
Create Date: 2025-12-18

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '450e2310a5af'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # This is a dummy migration to fix the KeyError on Railway.
    # It does nothing because the tables already exist.
    pass

def downgrade():
    pass