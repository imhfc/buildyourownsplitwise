"""add soft delete columns to groups and expenses

Revision ID: d4e5f6a7b8c9
Revises: e5f6a7b8c9d0
Create Date: 2026-04-02 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa


revision = 'd4e5f6a7b8c9'
down_revision = 'e5f6a7b8c9d0'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('groups', sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('expenses', sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column('expenses', 'deleted_at')
    op.drop_column('groups', 'deleted_at')
