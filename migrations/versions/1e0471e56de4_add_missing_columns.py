"""Initial Robust Sync

Revision ID: 1e0471e56de4
Revises: 450e2310a5af
Create Date: 2025-12-18

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector

# revision identifiers, used by Alembic.
revision = '1e0471e56de4'
down_revision = '450e2310a5af'
branch_labels = None
depends_on = None

def upgrade():
    # Get the current database connection and inspect it
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    existing_tables = inspector.get_table_names()

    # 1. Create Tables ONLY if they don't exist
    # This prevents 'poisoning' the Postgres transaction
    
    if 'user' not in existing_tables:
        op.create_table('user',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('full_name', sa.String(length=100), nullable=False),
            sa.Column('email', sa.String(length=120), nullable=False),
            sa.Column('phone_number', sa.String(length=15), nullable=False),
            sa.Column('password_hash', sa.String(length=200), nullable=True),
            sa.Column('role', sa.String(length=20), nullable=False),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('email'),
            sa.UniqueConstraint('phone_number')
        )

    if 'vehicle' not in existing_tables:
        op.create_table('vehicle',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('owner_id', sa.Integer(), nullable=True),
            sa.Column('license_plate', sa.String(length=10), nullable=False),
            sa.ForeignKeyConstraint(['owner_id'], ['user.id'], ),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('license_plate')
        )

    if 'ride' not in existing_tables:
        op.create_table('ride',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('driver_id', sa.Integer(), nullable=False),
            sa.Column('origin', sa.String(length=200), nullable=False),
            sa.Column('destination', sa.String(length=200), nullable=False),
            sa.Column('status', sa.String(length=20), nullable=False),
            sa.ForeignKeyConstraint(['driver_id'], ['user.id'], ),
            sa.PrimaryKeyConstraint('id')
        )

    if 'chat_message' not in existing_tables:
        op.create_table('chat_message',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('ride_id', sa.Integer(), nullable=False),
            sa.Column('sender_id', sa.Integer(), nullable=False),
            sa.Column('content', sa.Text(), nullable=False),
            sa.ForeignKeyConstraint(['ride_id'], ['ride.id'], ),
            sa.ForeignKeyConstraint(['sender_id'], ['user.id'], ),
            sa.PrimaryKeyConstraint('id')
        )

    # 2. Add the receiver_id column ONLY if it's missing
    if 'chat_message' in existing_tables:
        columns = [c['name'] for c in inspector.get_columns('chat_message')]
        if 'receiver_id' not in columns:
            op.add_column('chat_message', sa.Column('receiver_id', sa.Integer(), nullable=True))
            op.create_foreign_key('fk_chat_message_receiver', 'chat_message', 'user', ['receiver_id'], ['id'])

def downgrade():
    pass