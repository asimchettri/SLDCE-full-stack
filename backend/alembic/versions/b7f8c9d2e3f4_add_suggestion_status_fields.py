"""Add status fields to suggestions table

Revision ID: b7f8c9d2e3f4
Revises: 395f642c5ae5
Create Date: 2026-01-08 10:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'b7f8c9d2e3f4'
down_revision = '395f642c5ae5'  # Update this to your latest migration
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add status tracking fields to suggestions table"""
    
    # Add status column with default 'pending'
    op.add_column('suggestions', 
        sa.Column('status', sa.String(length=50), nullable=False, server_default='pending')
    )
    
    # Add reviewed_at column (nullable - only set when reviewed)
    op.add_column('suggestions',
        sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True)
    )
    
    # Add reviewer_notes column (nullable - optional notes)
    op.add_column('suggestions',
        sa.Column('reviewer_notes', sa.Text(), nullable=True)
    )
    
    # Create index on status for faster filtering
    op.create_index('ix_suggestions_status', 'suggestions', ['status'])


def downgrade() -> None:
    """Remove status tracking fields from suggestions table"""
    
    # Drop index
    op.drop_index('ix_suggestions_status', table_name='suggestions')
    
    # Drop columns
    op.drop_column('suggestions', 'reviewer_notes')
    op.drop_column('suggestions', 'reviewed_at')
    op.drop_column('suggestions', 'status')