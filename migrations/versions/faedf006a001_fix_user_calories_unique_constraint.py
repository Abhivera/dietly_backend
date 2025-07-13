"""fix_user_calories_unique_constraint

Revision ID: faedf006a001
Revises: 422386675f13
Create Date: 2025-07-13 03:04:37.792851

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'faedf006a001'
down_revision: Union[str, None] = '422386675f13'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
