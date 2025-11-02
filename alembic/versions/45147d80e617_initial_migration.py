"""Initial migration

Revision ID: 45147d80e617
Revises: 
Create Date: 2025-10-28 22:50:36.399603

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '45147d80e617'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create restaurants table
    op.create_table('restaurants',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('pdf_content', sa.Text(), nullable=False),
        sa.Column('design_description', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create generated_code table
    op.create_table('generated_code',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('restaurant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('component_name', sa.String(length=255), nullable=False),
        sa.Column('code_content', sa.Text(), nullable=False),
        sa.Column('file_path', sa.String(length=500), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['restaurant_id'], ['restaurants.id'], ),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('generated_code')
    op.drop_table('restaurants')
