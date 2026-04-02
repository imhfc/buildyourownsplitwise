"""add email_invitations table

Revision ID: c8d9e0f1a2b3
Revises: b7c8d9e0f1a2
Create Date: 2026-04-02 12:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


revision = 'c8d9e0f1a2b3'
down_revision = 'b7c8d9e0f1a2'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'email_invitations',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('group_id', UUID(as_uuid=True), sa.ForeignKey('groups.id'), nullable=False),
        sa.Column('inviter_id', UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('token', sa.String(64), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, server_default='pending'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('responded_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_email_invitations_email', 'email_invitations', ['email'])
    op.create_index('ix_email_invitations_token', 'email_invitations', ['token'], unique=True)
    op.create_index('ix_email_invitations_email_status', 'email_invitations', ['email', 'status'])


def downgrade() -> None:
    op.drop_index('ix_email_invitations_email_status', table_name='email_invitations')
    op.drop_index('ix_email_invitations_token', table_name='email_invitations')
    op.drop_index('ix_email_invitations_email', table_name='email_invitations')
    op.drop_table('email_invitations')
