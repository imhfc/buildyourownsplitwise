"""merge_expense_payers_and_remove_categories

Revision ID: a19964cea032
Revises: edcd9bdae053, h7i8j9k0l1m2
Create Date: 2026-04-02 17:08:40.996509

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a19964cea032'
down_revision: Union[str, None] = ('edcd9bdae053', 'h7i8j9k0l1m2')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
