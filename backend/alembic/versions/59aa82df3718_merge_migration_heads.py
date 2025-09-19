"""merge migration heads

Revision ID: 59aa82df3718
Revises: add_user_roles_rbac, new_auth_fields
Create Date: 2025-09-18 07:06:51.743309

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '59aa82df3718'
down_revision = ('add_user_roles_rbac', 'new_auth_fields')
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Upgrade database schema."""
    pass


def downgrade() -> None:
    """Downgrade database schema."""
    pass
