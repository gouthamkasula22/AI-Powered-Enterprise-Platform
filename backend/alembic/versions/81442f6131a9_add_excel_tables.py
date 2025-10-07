"""add_excel_tables

Revision ID: 81442f6131a9
Revises: 5c37977224fe
Create Date: 2025-10-06 17:18:42.804185

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '81442f6131a9'
down_revision = '5c37977224fe'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Upgrade database schema."""
    # Create excel_documents table
    op.create_table(
        'excel_documents',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('filename', sa.String(length=255), nullable=False),
        sa.Column('original_filename', sa.String(length=255), nullable=False),
        sa.Column('file_path', sa.String(length=500), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=False),
        sa.Column('mime_type', sa.String(length=100), nullable=False),
        sa.Column('sheet_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_rows', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_columns', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='uploaded'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('uploaded_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('processed_at', sa.DateTime(), nullable=True),
        sa.Column('last_accessed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_excel_documents_user_id'), 'excel_documents', ['user_id'], unique=False)
    
    # Create excel_sheets table
    op.create_table(
        'excel_sheets',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('document_id', sa.Integer(), nullable=False),
        sa.Column('sheet_name', sa.String(length=255), nullable=False),
        sa.Column('sheet_index', sa.Integer(), nullable=False),
        sa.Column('row_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('column_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('columns', sa.JSON(), nullable=True),
        sa.Column('column_types', sa.JSON(), nullable=True),
        sa.Column('statistics', sa.JSON(), nullable=True),
        sa.Column('semantic_types', sa.JSON(), nullable=True),
        sa.Column('key_columns', sa.JSON(), nullable=True),
        sa.Column('has_missing_values', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('missing_percentage', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('duplicate_rows', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.ForeignKeyConstraint(['document_id'], ['excel_documents.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_excel_sheets_document_id'), 'excel_sheets', ['document_id'], unique=False)
    
    # Create excel_queries table
    op.create_table(
        'excel_queries',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('document_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('query_text', sa.Text(), nullable=False),
        sa.Column('query_type', sa.String(length=50), nullable=True),
        sa.Column('target_sheet', sa.String(length=255), nullable=True),
        sa.Column('generated_code', sa.Text(), nullable=True),
        sa.Column('code_explanation', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='pending'),
        sa.Column('result', sa.JSON(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('execution_time_ms', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('executed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['document_id'], ['excel_documents.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_excel_queries_document_id'), 'excel_queries', ['document_id'], unique=False)
    op.create_index(op.f('ix_excel_queries_user_id'), 'excel_queries', ['user_id'], unique=False)
    op.create_index(op.f('ix_excel_queries_created_at'), 'excel_queries', ['created_at'], unique=False)
    
    # Create excel_visualizations table
    op.create_table(
        'excel_visualizations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('query_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('chart_type', sa.String(length=50), nullable=False),
        sa.Column('config', sa.JSON(), nullable=False),
        sa.Column('data', sa.JSON(), nullable=False),
        sa.Column('image_path', sa.String(length=500), nullable=True),
        sa.Column('image_format', sa.String(length=10), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['query_id'], ['excel_queries.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_excel_visualizations_query_id'), 'excel_visualizations', ['query_id'], unique=False)
    op.create_index(op.f('ix_excel_visualizations_user_id'), 'excel_visualizations', ['user_id'], unique=False)


def downgrade() -> None:
    """Downgrade database schema."""
    op.drop_index(op.f('ix_excel_visualizations_user_id'), table_name='excel_visualizations')
    op.drop_index(op.f('ix_excel_visualizations_query_id'), table_name='excel_visualizations')
    op.drop_table('excel_visualizations')
    
    op.drop_index(op.f('ix_excel_queries_created_at'), table_name='excel_queries')
    op.drop_index(op.f('ix_excel_queries_user_id'), table_name='excel_queries')
    op.drop_index(op.f('ix_excel_queries_document_id'), table_name='excel_queries')
    op.drop_table('excel_queries')
    
    op.drop_index(op.f('ix_excel_sheets_document_id'), table_name='excel_sheets')
    op.drop_table('excel_sheets')
    
    op.drop_index(op.f('ix_excel_documents_user_id'), table_name='excel_documents')
    op.drop_table('excel_documents')
