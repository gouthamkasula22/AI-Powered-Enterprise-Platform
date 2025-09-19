"""Add role-based access control to users table

Revision ID: add_user_roles_rbac
Revises: 053765c1e5b0
Create Date: 2025-09-18 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_user_roles_rbac'
down_revision = '053765c1e5b0'
branch_labels = None
depends_on = None


def upgrade():
    """Add role column and migrate existing users"""
    # Add role column with default value
    op.add_column('users', 
        sa.Column('role', sa.String(20), nullable=False, server_default='USER')
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


def downgrade():
    """Remove role column and restore legacy flags functionality"""
    # Note: We keep is_staff and is_superuser columns as they might be used elsewhere
    # Remove the index first
    op.drop_index('ix_users_role', table_name='users')
    
    # Drop the role column
    op.drop_column('users', 'role')