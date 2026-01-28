"""add_column_names_to_dataset

Revision ID: efb035d7b9b1
Revises: 5b7228d90e05
Create Date: 2026-01-26 15:57:57.080328

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'efb035d7b9b1'
down_revision: Union[str, None] = '5b7228d90e05'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.add_column('datasets', sa.Column('feature_names', sa.Text(), nullable=True))
    op.add_column('datasets', sa.Column('label_column_name', sa.String(255), nullable=True))


def downgrade():
    op.drop_column('datasets', 'label_column_name')
    op.drop_column('datasets', 'feature_names')
