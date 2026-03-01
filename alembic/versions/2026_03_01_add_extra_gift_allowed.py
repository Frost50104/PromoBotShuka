"""Add extra_gift_allowed to users

Revision ID: ae4fe6f30609
Revises: a1b2c3d4e5f6
Create Date: 2026-03-01 00:00:00.000000+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ae4fe6f30609'
down_revision: Union[str, None] = 'e2c5ed1daaab'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'users',
        sa.Column(
            'extra_gift_allowed',
            sa.Boolean(),
            nullable=False,
            server_default='false',
        )
    )


def downgrade() -> None:
    op.drop_column('users', 'extra_gift_allowed')
