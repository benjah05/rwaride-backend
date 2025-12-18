"""Initial Robust Sync

Revision ID: 1e0471e56de4
Revises: None
Create Date: 2025-12-18

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '1e0471e56de4'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # 1. Create Tables if they don't exist (Recovery Mode)
    # This ensures your local DB gets rebuilt if empty, 
    # but won't crash your Railway DB which already has these tables.
    
    try:
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
    except Exception:
        pass

    try:
        op.create_table('vehicle',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('owner_id', sa.Integer(), nullable=True),
            sa.Column('license_plate', sa.String(length=10), nullable=False),
            sa.ForeignKeyConstraint(['owner_id'], ['user.id'], ),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('license_plate')
        )
    except Exception:
        pass

    try:
        op.create_table('ride',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('driver_id', sa.Integer(), nullable=False),
            sa.Column('origin', sa.String(length=200), nullable=False),
            sa.Column('destination', sa.String(length=200), nullable=False),
            sa.Column('status', sa.String(length=20), nullable=False),
            sa.ForeignKeyConstraint(['driver_id'], ['user.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
    except Exception:
        pass

    try:
        op.create_table('chat_message',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('ride_id', sa.Integer(), nullable=False),
            sa.Column('sender_id', sa.Integer(), nullable=False),
            sa.Column('content', sa.Text(), nullable=False),
            sa.ForeignKeyConstraint(['ride_id'], ['ride.id'], ),
            sa.ForeignKeyConstraint(['sender_id'], ['user.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
    except Exception:
        pass

    # 2. Add the NEW column that started all this trouble
    try:
        op.add_column('chat_message', sa.Column('receiver_id', sa.Integer(), nullable=True))
        op.create_foreign_key('fk_chat_message_receiver', 'chat_message', 'user', ['receiver_id'], ['id'])
    except Exception:
        pass

def downgrade():
    pass