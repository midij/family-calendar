"""Recreate events table with JSON columns and indexes

Revision ID: 4353343424d8
Revises: 713dd026e380
Create Date: 2025-09-04 11:18:09.781692

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4353343424d8'
down_revision = '713dd026e380'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # For SQLite, we need to recreate the table to change column types
    # First, create a backup table with the new structure
    op.create_table('events_new',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('location', sa.String(), nullable=True),
        sa.Column('start_utc', sa.DateTime(timezone=True), nullable=False),
        sa.Column('end_utc', sa.DateTime(timezone=True), nullable=False),
        sa.Column('rrule', sa.String(), nullable=True),
        sa.Column('exdates', sa.JSON(), nullable=True),
        sa.Column('kid_ids', sa.JSON(), nullable=True),
        sa.Column('category', sa.String(), nullable=False),
        sa.Column('source', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Copy data from old table to new table (if old table exists)
    connection = op.get_bind()
    result = connection.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='events'")
    if result.fetchone():
        op.execute("""
            INSERT INTO events_new (id, created_at, updated_at, title, location, start_utc, end_utc, 
                                   rrule, exdates, kid_ids, category, source, created_by)
            SELECT id, created_at, updated_at, title, location, start_utc, end_utc, 
                   rrule, 
                   CASE WHEN exdates IS NOT NULL AND exdates != '' THEN json(exdates) ELSE NULL END,
                   CASE WHEN kid_ids IS NOT NULL AND kid_ids != '' THEN json(kid_ids) ELSE NULL END,
                   category, source, created_by
            FROM events
        """)
    
    # Drop the old table (if it exists)
    connection = op.get_bind()
    result = connection.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='events'")
    if result.fetchone():
        op.drop_table('events')
    
    # Rename the new table
    op.rename_table('events_new', 'events')
    
    # Create indexes
    op.create_index('ix_events_start_utc', 'events', ['start_utc'], unique=False)
    op.create_index('ix_events_end_utc', 'events', ['end_utc'], unique=False)
    op.create_index('ix_events_time_range', 'events', ['start_utc', 'end_utc'], unique=False)


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_events_time_range', table_name='events')
    op.drop_index('ix_events_end_utc', table_name='events')
    op.drop_index('ix_events_start_utc', table_name='events')
    
    # Recreate table with TEXT columns
    op.create_table('events_old',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('location', sa.String(), nullable=True),
        sa.Column('start_utc', sa.DateTime(timezone=True), nullable=False),
        sa.Column('end_utc', sa.DateTime(timezone=True), nullable=False),
        sa.Column('rrule', sa.String(), nullable=True),
        sa.Column('exdates', sa.Text(), nullable=True),
        sa.Column('kid_ids', sa.Text(), nullable=True),
        sa.Column('category', sa.String(), nullable=False),
        sa.Column('source', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Copy data back
    op.execute("""
        INSERT INTO events_old (id, created_at, updated_at, title, location, start_utc, end_utc, 
                               rrule, exdates, kid_ids, category, source, created_by)
        SELECT id, created_at, updated_at, title, location, start_utc, end_utc, 
               rrule, 
               CASE WHEN exdates IS NOT NULL THEN json_extract(exdates, '$') ELSE NULL END,
               CASE WHEN kid_ids IS NOT NULL THEN json_extract(kid_ids, '$') ELSE NULL END,
               category, source, created_by
        FROM events
    """)
    
    # Drop and rename
    op.drop_table('events')
    op.rename_table('events_old', 'events')
