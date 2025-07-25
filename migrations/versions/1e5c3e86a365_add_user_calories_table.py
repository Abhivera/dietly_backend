"""add user_calories table

Revision ID: 1e5c3e86a365
Revises: c0f474573279
Create Date: 2025-07-12 15:35:14.042678

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1e5c3e86a365'
down_revision: Union[str, None] = 'c0f474573279'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('user_calories',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('activity_date', sa.Date(), nullable=False),
    sa.Column('calories_burn', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_user_calories_activity_date'), 'user_calories', ['activity_date'], unique=False)
    op.create_index(op.f('ix_user_calories_id'), 'user_calories', ['id'], unique=False)
    op.create_index(op.f('ix_user_calories_user_id'), 'user_calories', ['user_id'], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_user_calories_user_id'), table_name='user_calories')
    op.drop_index(op.f('ix_user_calories_id'), table_name='user_calories')
    op.drop_index(op.f('ix_user_calories_activity_date'), table_name='user_calories')
    op.drop_table('user_calories')
    # ### end Alembic commands ###
