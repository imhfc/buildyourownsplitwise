"""add settlement status and rate locking columns

Revision ID: g6h7i8j9k0l1
Revises: a6b7c8d9e0f1, b7c8d9e0f1a2
Create Date: 2026-04-02 12:00:00.000000
"""
from alembic import op
import sqlalchemy as sa


revision = 'g6h7i8j9k0l1'
down_revision = ('a6b7c8d9e0f1', 'b7c8d9e0f1a2')
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 結算確認流程欄位
    op.add_column('settlements', sa.Column('status', sa.String(20), nullable=True))
    op.add_column('settlements', sa.Column('confirmed_at', sa.DateTime(timezone=True), nullable=True))

    # 統一幣別結算 — 匯率鎖定欄位
    op.add_column('settlements', sa.Column('original_currency', sa.String(3), nullable=True))
    op.add_column('settlements', sa.Column('original_amount', sa.Numeric(12, 2), nullable=True))
    op.add_column('settlements', sa.Column('locked_rate', sa.Numeric(18, 8), nullable=True))

    # 既有資料設為 confirmed（向後相容：舊結算視為已完成）
    op.execute("UPDATE settlements SET status = 'confirmed' WHERE status IS NULL")

    # 設定 NOT NULL + server_default（新建的 settlement 預設 pending）
    op.alter_column('settlements', 'status', nullable=False, server_default='pending')


def downgrade() -> None:
    op.drop_column('settlements', 'locked_rate')
    op.drop_column('settlements', 'original_amount')
    op.drop_column('settlements', 'original_currency')
    op.drop_column('settlements', 'confirmed_at')
    op.drop_column('settlements', 'status')
