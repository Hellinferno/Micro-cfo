"""Rename metadata column to meta_info in usage_logs

Revision ID: 375f898db4d4
Revises: 2ccceaa9b0b8
Create Date: 2026-01-31 18:57:19.633537

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '375f898db4d4'
down_revision: Union[str, Sequence[str], None] = '2ccceaa9b0b8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create usage_logs table if it doesn't exist, or rename column if it does
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    
    if 'usage_logs' in inspector.get_table_names():
        # Table exists - check if we need to rename the column
        columns = [col['name'] for col in inspector.get_columns('usage_logs')]
        if 'metadata' in columns and 'meta_info' not in columns:
            op.alter_column('usage_logs', 'metadata', new_column_name='meta_info')
    else:
        # Table doesn't exist - create it with meta_info column
        op.create_table('usage_logs',
            sa.Column('id', sa.UUID(), nullable=False),
            sa.Column('user_id', sa.UUID(), nullable=True),
            sa.Column('route', sa.String(length=255), nullable=False),
            sa.Column('method', sa.String(length=10), nullable=False),
            sa.Column('status_code', sa.Integer(), nullable=True),
            sa.Column('model_used', sa.String(length=100), nullable=True),
            sa.Column('input_tokens', sa.Integer(), nullable=True),
            sa.Column('output_tokens', sa.Integer(), nullable=True),
            sa.Column('total_cost_usd', sa.Numeric(precision=12, scale=6), nullable=True),
            sa.Column('duration_ms', sa.Float(), nullable=True),
            sa.Column('request_id', sa.String(length=100), nullable=True),
            sa.Column('meta_info', sa.JSON(), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index('idx_usage_logs_user_created', 'usage_logs', ['user_id', 'created_at'], unique=False)
        op.create_index(op.f('ix_usage_logs_created_at'), 'usage_logs', ['created_at'], unique=False)
        op.create_index(op.f('ix_usage_logs_user_id'), 'usage_logs', ['user_id'], unique=False)
    
    # Create golden_dataset table if it doesn't exist
    if 'golden_dataset' not in inspector.get_table_names():
        op.create_table('golden_dataset',
            sa.Column('id', sa.UUID(), nullable=False),
            sa.Column('user_id', sa.UUID(), nullable=True),
            sa.Column('invoice_id', sa.UUID(), nullable=True),
            sa.Column('model_used', sa.String(length=100), nullable=True),
            sa.Column('original_data', sa.JSON(), nullable=False),
            sa.Column('corrected_data', sa.JSON(), nullable=False),
            sa.Column('notes', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
            sa.ForeignKeyConstraint(['invoice_id'], ['invoices.id'], ondelete='SET NULL'),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index('idx_golden_dataset_user_created', 'golden_dataset', ['user_id', 'created_at'], unique=False)
        op.create_index(op.f('ix_golden_dataset_created_at'), 'golden_dataset', ['created_at'], unique=False)
        op.create_index(op.f('ix_golden_dataset_invoice_id'), 'golden_dataset', ['invoice_id'], unique=False)
        op.create_index(op.f('ix_golden_dataset_user_id'), 'golden_dataset', ['user_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    
    if 'usage_logs' in inspector.get_table_names():
        columns = [col['name'] for col in inspector.get_columns('usage_logs')]
        if 'meta_info' in columns:
            op.alter_column('usage_logs', 'meta_info', new_column_name='metadata')
    
    # Note: We don't drop the tables in downgrade to preserve data
    # If you want to drop them, uncomment below:
    # op.drop_index(op.f('ix_golden_dataset_user_id'), table_name='golden_dataset')
    # op.drop_index(op.f('ix_golden_dataset_invoice_id'), table_name='golden_dataset')
    # op.drop_index(op.f('ix_golden_dataset_created_at'), table_name='golden_dataset')
    # op.drop_index('idx_golden_dataset_user_created', table_name='golden_dataset')
    # op.drop_table('golden_dataset')
    # op.drop_index(op.f('ix_usage_logs_user_id'), table_name='usage_logs')
    # op.drop_index(op.f('ix_usage_logs_created_at'), table_name='usage_logs')
    # op.drop_index('idx_usage_logs_user_created', table_name='usage_logs')
    # op.drop_table('usage_logs')
