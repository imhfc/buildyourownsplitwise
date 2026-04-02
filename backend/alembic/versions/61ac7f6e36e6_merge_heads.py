"""merge_heads

Revision ID: 61ac7f6e36e6
Revises: c8d9e0f1a2b3, g6h7i8j9k0l1
Create Date: 2026-04-02 16:20:54.516073

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '61ac7f6e36e6'
down_revision: Union[str, None] = ('c8d9e0f1a2b3', 'g6h7i8j9k0l1')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
