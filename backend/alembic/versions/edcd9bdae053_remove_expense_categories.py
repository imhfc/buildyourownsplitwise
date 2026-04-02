"""remove_expense_categories

Revision ID: edcd9bdae053
Revises: 61ac7f6e36e6
Create Date: 2026-04-02 16:20:58.229455

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'edcd9bdae053'
down_revision: Union[str, None] = '61ac7f6e36e6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint("expenses_category_id_fkey", "expenses", type_="foreignkey")
    op.drop_column("expenses", "category_id")
    op.drop_table("expense_categories")


def downgrade() -> None:
    op.create_table(
        "expense_categories",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(50), nullable=False),
        sa.Column("icon", sa.String(50), nullable=True),
        sa.Column("color", sa.String(7), nullable=True),
        sa.Column("is_default", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("group_id", sa.UUID(), sa.ForeignKey("groups.id"), nullable=True),
        sa.Column("created_by", sa.UUID(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.add_column("expenses", sa.Column("category_id", sa.UUID(), nullable=True))
    op.create_foreign_key(
        "expenses_category_id_fkey", "expenses", "expense_categories",
        ["category_id"], ["id"], ondelete="SET NULL",
    )
