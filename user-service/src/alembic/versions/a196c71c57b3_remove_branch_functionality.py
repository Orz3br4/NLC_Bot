"""remove_branch_functionality

Revision ID: a196c71c57b3
Revises: e565c0452c62
Create Date: 2025-06-09 17:03:34.402002

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a196c71c57b3'
down_revision: Union[str, None] = 'e565c0452c62'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Get database connection
    connection = op.get_bind()
    
    # First, update all districts to have no parent (set parent_unit_id = NULL)
    # This removes the branch level from the hierarchy
    connection.execute(
        sa.text("""
            UPDATE organization_units 
            SET parent_unit_id = NULL 
            WHERE category_id = 2 AND parent_unit_id IS NOT NULL
        """)
    )
    
    # Move any users directly assigned to branch units to their district units
    # This assumes each branch has at least one district
    connection.execute(
        sa.text("""
            UPDATE user_organization_units 
            SET unit_id = (
                SELECT districts.id 
                FROM organization_units branches 
                JOIN organization_units districts ON districts.parent_unit_id = branches.id 
                WHERE branches.id = user_organization_units.unit_id 
                AND branches.category_id = 1 
                AND districts.category_id = 2 
                LIMIT 1
            )
            WHERE unit_id IN (
                SELECT id FROM organization_units WHERE category_id = 1
            )
        """)
    )
    
    # Delete branch units (category_id = 1)
    connection.execute(
        sa.text("DELETE FROM organization_units WHERE category_id = 1")
    )
    
    # Delete branch category (category_id = 1) if it exists
    connection.execute(
        sa.text("DELETE FROM organization_categories WHERE id = 1")
    )


def downgrade() -> None:
    # This downgrade recreates the branch structure
    # NOTE: This is a destructive operation and may not perfectly restore the original structure
    
    connection = op.get_bind()
    
    # Recreate branch category
    connection.execute(
        sa.text("""
            INSERT INTO organization_categories (id, category_name, created_at) 
            VALUES (1, '分堂', NOW()) 
            ON CONFLICT (id) DO NOTHING
        """)
    )
    
    # Create a default branch unit
    connection.execute(
        sa.text("""
            INSERT INTO organization_units (unit_name, category_id, parent_unit_id, created_at) 
            VALUES ('預設分堂', 1, NULL, NOW()) 
            RETURNING id
        """)
    )
    
    # Get the new branch ID
    result = connection.execute(sa.text("SELECT id FROM organization_units WHERE category_id = 1 LIMIT 1"))
    branch_id = result.fetchone()[0]
    
    # Update all districts to be under this branch
    connection.execute(
        sa.text(f"""
            UPDATE organization_units 
            SET parent_unit_id = {branch_id} 
            WHERE category_id = 2 AND parent_unit_id IS NULL
        """)
    )
