"""add_role_column_to_users

Revision ID: 5c37977224fe
Revises: 6b400376be29
Create Date: 2025-10-05 16:41:21.506712

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5c37977224fe'
down_revision = '6b400376be29'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Upgrade database schema."""
    # Add role column with default value
    op.add_column('users', 
        sa.Column('role', sa.String(50), nullable=False, server_default='USER')
    )
    
    # Create index for performance
    op.create_index('ix_users_role', 'users', ['role'])
    
    # Migrate existing data from legacy boolean flags to new role system
    # Priority: is_superuser > is_staff > default user
    op.execute("""
        UPDATE users 
        SET role = CASE 
            WHEN is_superuser = true THEN 'SUPERADMIN'
            WHEN is_staff = true THEN 'ADMIN'
            ELSE 'USER'
        END
    """)
    
    # Remove server default after migration (we want explicit role assignment)
    op.alter_column('users', 'role', server_default=None)


def downgrade() -> None:
    """Downgrade database schema."""
    # Remove the index first
    op.drop_index('ix_users_role', table_name='users')
    
    # Drop the role column
    op.drop_column('users', 'role')
