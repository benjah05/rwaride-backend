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
    
    # Get tables in the 'public' schema (common for Railway Postgres)
    existing_tables = inspector.get_table_names()

    # 1. Create Core Tables ONLY if they don't exist
    if 'user' not in existing_tables:
        op.create_table('user',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('full_name', sa.String(length=100), nullable=False),
            sa.Column('email', sa.String(length=120), nullable=False),
            sa.Column('phone_number', sa.String(length=15), nullable=False),
            sa.Column('password_hash', sa.String(length=200), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('role', sa.String(length=20), nullable=False),
            sa.Column('is_identity_verified', sa.Boolean(), nullable=True, server_default='false'),
            sa.Column('driver_license_id', sa.String(length=50), nullable=True),
            sa.Column('is_license_verified', sa.Boolean(), nullable=True, server_default='false'),
            sa.Column('bio', sa.Text(), nullable=True),
            sa.Column('average_rating', sa.Float(), nullable=True, server_default='5.0'),
            sa.Column('total_ride_count', sa.Integer(), nullable=True, server_default='0'),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('email'),
            sa.UniqueConstraint('phone_number'),
            sa.UniqueConstraint('driver_license_id')
        )

    if 'vehicle' not in existing_tables:
        op.create_table('vehicle',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('owner_id', sa.Integer(), nullable=True),
            sa.Column('make', sa.String(length=50), nullable=True),
            sa.Column('model', sa.String(length=50), nullable=True),
            sa.Column('year', sa.Integer(), nullable=True),
            sa.Column('color', sa.String(length=30), nullable=True),
            sa.Column('license_plate', sa.String(length=10), nullable=False),
            sa.Column('seat_capacity', sa.Integer(), nullable=False, server_default='4'),
            sa.Column('is_verified', sa.Boolean(), nullable=True, server_default='false'),
            sa.ForeignKeyConstraint(['owner_id'], ['user.id'], ),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('license_plate')
        )

    if 'ride' not in existing_tables:
        op.create_table('ride',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('driver_id', sa.Integer(), nullable=False),
            sa.Column('vehicle_id', sa.Integer(), nullable=True),
            sa.Column('origin', sa.String(length=200), nullable=False),
            sa.Column('destination', sa.String(length=200), nullable=False),
            sa.Column('departure_time', sa.DateTime(timezone=True), nullable=False),
            sa.Column('total_seats', sa.Integer(), nullable=False),
            sa.Column('available_seats', sa.Integer(), nullable=False),
            sa.Column('status', sa.String(length=20), nullable=False, server_default='open'),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
            sa.ForeignKeyConstraint(['driver_id'], ['user.id'], ),
            sa.ForeignKeyConstraint(['vehicle_id'], ['vehicle.id'], ondelete='SET NULL'),
            sa.PrimaryKeyConstraint('id')
        )

    if 'driver_location' not in existing_tables:
        op.create_table('driver_location',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('driver_id', sa.Integer(), nullable=False),
            sa.Column('latitude', sa.Float(), nullable=False),
            sa.Column('longitude', sa.Float(), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
            sa.ForeignKeyConstraint(['driver_id'], ['user.id'], ),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('driver_id')
        )

    if 'passenger_ride' not in existing_tables:
        op.create_table('passenger_ride',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('passenger_id', sa.Integer(), nullable=False),
            sa.Column('ride_id', sa.Integer(), nullable=False),
            sa.Column('seats_booked', sa.Integer(), nullable=False, server_default='1'),
            sa.Column('status', sa.String(length=20), nullable=False, server_default='booked'),
            sa.Column('booked_at', sa.DateTime(timezone=True), nullable=True),
            sa.ForeignKeyConstraint(['passenger_id'], ['user.id'], ),
            sa.ForeignKeyConstraint(['ride_id'], ['ride.id'], ),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('passenger_id', 'ride_id', name='uq_passenger_ride_booking')
        )

    if 'chat_message' not in existing_tables:
        op.create_table('chat_message',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('ride_id', sa.Integer(), nullable=False),
            sa.Column('sender_id', sa.Integer(), nullable=False),
            sa.Column('content', sa.Text(), nullable=False),
            sa.Column('timestamp', sa.DateTime(timezone=True), nullable=True),
            sa.ForeignKeyConstraint(['ride_id'], ['ride.id'], ),
            sa.ForeignKeyConstraint(['sender_id'], ['user.id'], ),
            sa.PrimaryKeyConstraint('id')
        )

    if 'review' not in existing_tables:
        op.create_table('review',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('ride_id', sa.Integer(), nullable=False),
            sa.Column('reviewer_id', sa.Integer(), nullable=False),
            sa.Column('reviewee_id', sa.Integer(), nullable=False),
            sa.Column('rating', sa.Integer(), nullable=False),
            sa.Column('comment', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
            sa.ForeignKeyConstraint(['reviewee_id'], ['user.id'], ),
            sa.ForeignKeyConstraint(['reviewer_id'], ['user.id'], ),
            sa.ForeignKeyConstraint(['ride_id'], ['ride.id'], ),
            sa.PrimaryKeyConstraint('id')
        )

    # 2. Add specific columns if missing
    if 'chat_message' in existing_tables:
        c_cols = [c['name'] for c in inspector.get_columns('chat_message')]
        if 'receiver_id' not in c_cols:
            op.add_column('chat_message', sa.Column('receiver_id', sa.Integer(), nullable=True))
            op.create_foreign_key('fk_chat_message_receiver', 'chat_message', 'user', ['receiver_id'], ['id'])

def downgrade():
    pass