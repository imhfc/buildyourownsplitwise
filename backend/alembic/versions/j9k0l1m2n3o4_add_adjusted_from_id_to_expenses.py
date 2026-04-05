"""add_adjusted_from_id_to_expenses

Revision ID: j9k0l1m2n3o4
Revises: af2b679ea093
Create Date: 2026-04-05 22:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'j9k0l1m2n3o4'
down_revision: Union[str, None] = 'af2b679ea093'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('expenses', sa.Column(
        'adjusted_from_id',
        postgresql.UUID(as_uuid=True),
        sa.ForeignKey('expenses.id'),
        nullable=True,
    ))
    op.create_index('ix_expenses_adjusted_from_id', 'expenses', ['adjusted_from_id'])


def downgrade() -> None:
    op.drop_index('ix_expenses_adjusted_from_id', table_name='expenses')
    op.drop_column('expenses', 'adjusted_from_id')
