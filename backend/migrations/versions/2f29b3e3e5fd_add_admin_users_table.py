"""add admin_users table

Revision ID: 2f29b3e3e5fd
Revises: 0002_replace_with_full_schema
Create Date: 2026-08-07 21:25:37.439559

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2f29b3e3e5fd'
down_revision: Union[str, None] = '0002_replace_with_full_schema'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'admin_users',
        sa.Column('admin_id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('username', sa.String(length=50), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('role', sa.String(length=20), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('admin_id'),
    )
    op.create_index(
        op.f('ix_admin_users_username'), 'admin_users', ['username'], unique=True
    )


def downgrade() -> None:
    op.drop_index(op.f('ix_admin_users_username'), table_name='admin_users')
    op.drop_table('admin_users')