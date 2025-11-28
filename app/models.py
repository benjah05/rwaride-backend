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
    
    # Verification status for insurance/registration check
    is_verified = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f'<Vehicle {self.make} {self.model} ({self.license_plate})>'