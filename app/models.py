from app import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model):
    """
    Represents a user on the carpooling platform, who can be a passenger, a driver, or both.
    """
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone_number = db.Column(db.String(15), unique=True, nullable=False)
    password_hash = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    # Role: 'passenger', 'driver', or 'both'
    role = db.Column(db.String(20), default='passenger', nullable=False)
    # Identity Verification Status (for safety/trust)
    is_identity_verified = db.Column(db.Boolean, default=False)

    # Driver Specifics (if role includes 'driver')
    driver_license_id = db.Column(db.String(50), unique=True, nullable=True)
    is_license_verified = db.Column(db.Boolean, default=False)
    # Profile Details
    bio = db.Column(db.Text, nullable=True)

    # Reputation and Experience
    average_rating = db.Column(db.Float, default=5.0) 
    total_ride_count = db.Column(db.Integer, default=0)

    # Relationships (drivers can have multiple vehicles)
    vehicles = db.relationship('Vehicle', backref='owner', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.full_name} ({self.role})>'
    
class Vehicle(db.Model):
    """
    Represents a vehicle registered by a driver.
    """
    id = db.Column(db.Integer, primary_key=True)
    # This foreign key links the vehicle back to its owner
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id')) 
    
    # Optional fields
    make = db.Column(db.String(50), nullable=True)
    model = db.Column(db.String(50), nullable=True)
    year = db.Column(db.Integer, nullable=True)
    color = db.Column(db.String(30), nullable=True)
    
    # Mandatory fields
    license_plate = db.Column(db.String(10), unique=True, nullable=False)
    seat_capacity = db.Column(db.Integer, default=4, nullable=False)
    
    is_verified = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f'<Vehicle {self.make} {self.model} ({self.license_plate})>'
    
class Ride(db.Model):
    """Represents a single ride/trip posted by a driver."""
    __tablename__ = 'ride'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Foreign Keys
    driver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    vehicle_id = db.Column(db.Integer, db.ForeignKey('vehicle.id'), nullable=True) 

    # Trip Details
    origin = db.Column(db.String(200), nullable=False)
    destination = db.Column(db.String(200), nullable=False)
    departure_time = db.Column(db.DateTime, nullable=False)
    
    # Capacity and Status
    total_seats = db.Column(db.Integer, nullable=False)
    available_seats = db.Column(db.Integer, nullable=False)
    
    # Status: 'open', 'full', 'completed', 'canceled'
    status = db.Column(db.String(20), default='open', nullable=False) 
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship to bookings via the join table (PassengerRide)
    bookings = db.relationship('PassengerRide', backref='ride', lazy='dynamic')

    def to_dict(self):
        return {
            'id': self.id,
            'driver_id': self.driver_id,
            'vehicle_id': self.vehicle_id,
            'origin': self.origin,
            'destination': self.destination,
            'departure_time': self.departure_time.isoformat(),
            'available_seats': self.available_seats,
            'status': self.status
        }
        
class PassengerRide(db.Model):
    """The join table for users (passengers) and rides (bookings)."""
    __tablename__ = 'passenger_ride'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Foreign Keys
    passenger_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    ride_id = db.Column(db.Integer, db.ForeignKey('ride.id'), nullable=False)
    
    # Booking Details
    seats_booked = db.Column(db.Integer, default=1, nullable=False)
    # Status: 'booked', 'confirmed', 'canceled', 'completed'
    status = db.Column(db.String(20), default='booked', nullable=False)
    booked_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Ensure a passenger can only book one entry per ride
    __table_args__ = (
        db.UniqueConstraint('passenger_id', 'ride_id', name='uq_passenger_ride_booking'),
    )