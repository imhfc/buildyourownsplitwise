"""add_color_scheme_theme_mode_to_users

Revision ID: af2b679ea093
Revises: 19ab5705135e
Create Date: 2026-04-05 15:18:22.349626

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'af2b679ea093'
down_revision: Union[str, None] = '19ab5705135e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('color_scheme', sa.String(20), nullable=False, server_default='blue'))
    op.add_column('users', sa.Column('theme_mode', sa.String(10), nullable=False, server_default='system'))


def downgrade() -> None:
    op.drop_column('users', 'theme_mode')
    op.drop_column('users', 'color_scheme')
