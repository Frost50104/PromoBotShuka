"""Add admins table

Revision ID: a1b2c3d4e5f6
Revises: 77866ebe91d5
Create Date: 2026-02-06 19:00:00.000000+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '77866ebe91d5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create admins table
    op.create_table('admins',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('telegram_id', sa.BigInteger(), nullable=False),
        sa.Column('first_name', sa.String(length=255), nullable=True),
        sa.Column('username', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_admins_telegram_id'), 'admins', ['telegram_id'], unique=True)

    # Insert initial admin
    op.execute("""
        INSERT INTO admins (telegram_id, first_name)
        VALUES (854825784, 'Initial Admin')
    """)


def downgrade() -> None:
    # Drop admins table
    op.drop_index(op.f('ix_admins_telegram_id'), table_name='admins')
    op.drop_table('admins')
