"""merge_detection_and_suggestion_migrations

Revision ID: 5b7228d90e05
Revises: 8f110729c9cf, b7f8c9d2e3f4
Create Date: 2026-01-08 11:49:16.856912

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5b7228d90e05'
down_revision: Union[str, None] = ('8f110729c9cf', 'b7f8c9d2e3f4')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
