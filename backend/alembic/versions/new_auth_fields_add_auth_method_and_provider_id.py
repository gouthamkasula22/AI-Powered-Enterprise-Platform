"""add auth method and provider id to users

Revision ID: new_auth_fields
Revises: 54203d44f987
Create Date: 2025-01-18 15:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'new_auth_fields'
down_revision = '54203d44f987'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add auth_method and auth_provider_id columns to users table."""
    # Add auth_method column with default value 'PASSWORD'
    op.add_column('users', sa.Column('auth_method', sa.String(length=50), nullable=False, server_default='PASSWORD'))
    
    # Add auth_provider_id column (nullable for password-based users)
    op.add_column('users', sa.Column('auth_provider_id', sa.String(length=255), nullable=True))
    
    # Create index on auth_method for faster queries
    op.create_index('idx_users_auth_method', 'users', ['auth_method'])


def downgrade() -> None:
    """Remove auth_method and auth_provider_id columns from users table."""
    # Drop index first
    op.drop_index('idx_users_auth_method', 'users')
    
    # Drop columns
    op.drop_column('users', 'auth_provider_id')
    op.drop_column('users', 'auth_method')