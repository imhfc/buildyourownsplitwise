"""add expense_payers table for multi-payer support

Revision ID: h7i8j9k0l1m2
Revises: g6h7i8j9k0l1
Create Date: 2026-04-02 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision: str = "h7i8j9k0l1m2"
down_revision: Union[str, None] = "g6h7i8j9k0l1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "expense_payers",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("expense_id", UUID(as_uuid=True), sa.ForeignKey("expenses.id"), nullable=False),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("expense_payers")
