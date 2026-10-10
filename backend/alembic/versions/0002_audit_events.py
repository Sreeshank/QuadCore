"""Owner-scoped action history; no financial values in event metadata."""
from alembic import op
import sqlalchemy as sa
revision = '0002'
down_revision = '0001'
branch_labels = None
depends_on = None

def upgrade():
    op.create_table('audit_events',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(64), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('action', sa.String(60), nullable=False),
        sa.Column('resource_id', sa.String(64), nullable=True),
        sa.Column('details_json', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False))
    op.create_index('ix_audit_events_user_id', 'audit_events', ['user_id'])

def downgrade():
    op.drop_index('ix_audit_events_user_id', table_name='audit_events')
    op.drop_table('audit_events')

