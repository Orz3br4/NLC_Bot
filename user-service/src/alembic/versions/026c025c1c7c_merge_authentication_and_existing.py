"""merge authentication and existing migrations

Revision ID: 026c025c1c7c
Revises: e565c0452c62, f1a2b3c4d5e6
Create Date: 2024-01-01 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '026c025c1c7c'
down_revision = ('e565c0452c62', 'f1a2b3c4d5e6')
branch_labels = None
depends_on = None


def upgrade() -> None:
    # This is a merge migration - no operations needed
    pass


def downgrade() -> None:
    # This is a merge migration - no operations needed
    pass