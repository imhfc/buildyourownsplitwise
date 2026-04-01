"""add invite_token to groups

Revision ID: e5f6a7b8c9d0
Revises: c3d4e5f6a7b8
Create Date: 2026-04-01 18:00:00.000000
"""
from alembic import op
import sqlalchemy as sa


revision = 'e5f6a7b8c9d0'
down_revision = 'c3d4e5f6a7b8'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('groups', sa.Column('invite_token', sa.String(32), nullable=True))
    op.add_column('groups', sa.Column('invite_token_created_at', sa.DateTime(timezone=True), nullable=True))
    op.create_index('ix_groups_invite_token', 'groups', ['invite_token'], unique=True)


def downgrade() -> None:
    op.drop_index('ix_groups_invite_token', table_name='groups')
    op.drop_column('groups', 'invite_token_created_at')
    op.drop_column('groups', 'invite_token')
