"""add expense_categories table and category_id to expenses

Revision ID: f5a6b7c8d9e0
Revises: d4e5f6a7b8c9
Create Date: 2026-04-02 00:00:01.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


revision = 'f5a6b7c8d9e0'
down_revision = 'd4e5f6a7b8c9'
branch_labels = None
depends_on = None

# 預設分類種子資料
DEFAULT_CATEGORIES = [
    {"name": "general", "icon": "receipt", "color": "#6B7280"},
    {"name": "food", "icon": "utensils", "color": "#EF4444"},
    {"name": "transport", "icon": "car", "color": "#3B82F6"},
    {"name": "housing", "icon": "home", "color": "#8B5CF6"},
    {"name": "entertainment", "icon": "gamepad", "color": "#F59E0B"},
    {"name": "shopping", "icon": "shopping-bag", "color": "#EC4899"},
    {"name": "utilities", "icon": "zap", "color": "#10B981"},
    {"name": "health", "icon": "heart", "color": "#EF4444"},
    {"name": "travel", "icon": "plane", "color": "#06B6D4"},
    {"name": "education", "icon": "book", "color": "#6366F1"},
    {"name": "other", "icon": "more-horizontal", "color": "#9CA3AF"},
]


def upgrade() -> None:
    # 建立 expense_categories 表
    op.create_table(
        'expense_categories',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('name', sa.String(50), nullable=False),
        sa.Column('icon', sa.String(50), nullable=True),
        sa.Column('color', sa.String(7), nullable=True),
        sa.Column('is_default', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('group_id', UUID(as_uuid=True), sa.ForeignKey('groups.id'), nullable=True),
        sa.Column('created_by', UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # 插入預設分類
    expense_categories = sa.table(
        'expense_categories',
        sa.column('name', sa.String),
        sa.column('icon', sa.String),
        sa.column('color', sa.String),
        sa.column('is_default', sa.Boolean),
    )
    op.bulk_insert(expense_categories, [
        {"name": c["name"], "icon": c["icon"], "color": c["color"], "is_default": True}
        for c in DEFAULT_CATEGORIES
    ])

    # 在 expenses 表加入 category_id FK
    op.add_column('expenses', sa.Column('category_id', UUID(as_uuid=True), nullable=True))
    op.create_foreign_key(
        'fk_expenses_category_id',
        'expenses', 'expense_categories',
        ['category_id'], ['id'],
    )


def downgrade() -> None:
    op.drop_constraint('fk_expenses_category_id', 'expenses', type_='foreignkey')
    op.drop_column('expenses', 'category_id')
    op.drop_table('expense_categories')
