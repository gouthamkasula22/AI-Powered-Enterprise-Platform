"""add_last_logout_field

Revision ID: 8287f2a893f9
Revises: 59aa82df3718
Create Date: 2025-09-22 17:41:53.463435

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8287f2a893f9'
down_revision = '59aa82df3718'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Upgrade database schema."""
    # Add last_logout column to users table
    op.add_column(
        'users',
        sa.Column('last_logout', sa.DateTime(timezone=True), nullable=True)
    )


def downgrade() -> None:
    """Downgrade database schema."""
    # Remove last_logout column from users table
    op.drop_column('users', 'last_logout')
