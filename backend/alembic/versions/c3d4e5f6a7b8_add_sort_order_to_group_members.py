"""add sort_order to group_members

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-04-01 12:00:00.000000
"""
from alembic import op
import sqlalchemy as sa


revision = 'c3d4e5f6a7b8'
down_revision = 'b2c3d4e5f6a7'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Drop pinned_at if it exists (from earlier iteration)
    try:
        op.drop_column('group_members', 'pinned_at')
    except Exception:
        pass
    op.add_column('group_members', sa.Column('sort_order', sa.Integer(), server_default='0', nullable=False))


def downgrade() -> None:
    op.drop_column('group_members', 'sort_order')
