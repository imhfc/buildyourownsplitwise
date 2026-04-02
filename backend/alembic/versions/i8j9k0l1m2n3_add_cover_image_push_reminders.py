"""add cover_image_url, push_token, payment_reminders

Revision ID: i8j9k0l1m2n3
Revises: h7i8j9k0l1m2
Create Date: 2026-04-02 16:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision: str = "i8j9k0l1m2n3"
down_revision: Union[str, None] = "h7i8j9k0l1m2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 群組封面照片
    op.add_column("groups", sa.Column("cover_image_url", sa.String(500), nullable=True))

    # Push token
    op.add_column("users", sa.Column("push_token", sa.String(255), nullable=True))

    # 付款提醒
    op.create_table(
        "payment_reminders",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("group_id", UUID(as_uuid=True), sa.ForeignKey("groups.id"), nullable=False),
        sa.Column("from_user", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("to_user", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("payment_reminders")
    op.drop_column("users", "push_token")
    op.drop_column("groups", "cover_image_url")
