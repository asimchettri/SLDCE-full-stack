"""add benchmark_results table

Revision ID: a1b2c3d4e5f6
Revises: <put your last revision id here>
Create Date: 2025-01-01 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = 'a1b2c3d4e5f6'
down_revision = 'efb035d7b9b1'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'benchmark_results',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('dataset_id', sa.Integer(), nullable=False),
        sa.Column('tool', sa.String(50), nullable=False),
        sa.Column('iteration', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('precision', sa.Float(), nullable=True),
        sa.Column('recall', sa.Float(), nullable=True),
        sa.Column('accuracy', sa.Float(), nullable=True),
        sa.Column('f1', sa.Float(), nullable=True),
        sa.Column('human_effort', sa.Integer(), nullable=True),
        sa.Column('meta', sa.Text(), nullable=True),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=True
        ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        'ix_benchmark_results_id',
        'benchmark_results', ['id']
    )
    op.create_index(
        'ix_benchmark_results_dataset_id',
        'benchmark_results', ['dataset_id']
    )


def downgrade() -> None:
    op.drop_index('ix_benchmark_results_dataset_id', table_name='benchmark_results')
    op.drop_index('ix_benchmark_results_id', table_name='benchmark_results')
    op.drop_table('benchmark_results')