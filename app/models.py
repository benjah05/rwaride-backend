from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

# Database initialization
db = SQLAlchemy()

class User(db.Model):
    """
    Represents a user on the carpooling platform.
    """
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone_number = db.Column(db.String(15), unique=True, nullable=False)
    password_hash = db.Column(db.String(200))
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    role = db.Column(db.String(20), default='passenger', nullable=False)
    is_identity_verified = db.Column(db.Boolean, default=False)

    # Driver Specifics
    driver_license_id = db.Column(db.String(50), unique=True, nullable=True)
    is_license_verified = db.Column(db.Boolean, default=False)
    bio = db.Column(db.Text, nullable=True)

    average_rating = db.Column(db.Float, default=5.0) 
    total_ride_count = db.Column(db.Integer, default=0)

    # Relationships
    vehicles = db.relationship('Vehicle', backref='owner', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def update_rating(self):
        reviews = Review.query.filter_by(reviewee_id=self.id).all()
        if reviews:
            self.average_rating = sum(r.rating for r in reviews) / len(reviews)

    def __repr__(self):
        return f'<User {self.full_name} ({self.role})>'
    
class Vehicle(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id')) 
    
    make = db.Column(db.String(50), nullable=True)
    model = db.Column(db.String(50), nullable=True)
    year = db.Column(db.Integer, nullable=True)
    color = db.Column(db.String(30), nullable=True)
    license_plate = db.Column(db.String(10), unique=True, nullable=False)
    seat_capacity = db.Column(db.Integer, default=4, nullable=False)
    is_verified = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f'<Vehicle {self.make} {self.model} ({self.license_plate})>'
    
class Ride(db.Model):
    __tablename__ = 'ride'
    
    id = db.Column(db.Integer, primary_key=True)
    driver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    vehicle_id = db.Column(db.Integer, db.ForeignKey('vehicle.id', ondelete='SET NULL'), nullable=True) 

    origin = db.Column(db.String(200), nullable=False)
    destination = db.Column(db.String(200), nullable=False)
    departure_time = db.Column(db.DateTime(timezone=True), nullable=False)
    
    total_seats = db.Column(db.Integer, nullable=False)
    available_seats = db.Column(db.Integer, nullable=False)
    
    status = db.Column(db.String(20), default='open', nullable=False) 
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    bookings = db.relationship('PassengerRide', backref='ride', lazy='dynamic')

    def book_seats(self, count):
        if self.available_seats >= count:
            self.available_seats -= count
            if self.available_seats == 0:
                self.status = 'full'
            return True
        return False

    def is_user_booked(self, user_id):
        return self.bookings.filter_by(passenger_id=user_id).first() is not None

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
    __tablename__ = 'passenger_ride'
    
    id = db.Column(db.Integer, primary_key=True)
    passenger_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    ride_id = db.Column(db.Integer, db.ForeignKey('ride.id'), nullable=False)
    
    seats_booked = db.Column(db.Integer, default=1, nullable=False)
    status = db.Column(db.String(20), default='booked', nullable=False)
    booked_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    __table_args__ = (
        db.UniqueConstraint('passenger_id', 'ride_id', name='uq_passenger_ride_booking'),
    )

class DriverLocation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    driver_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True, nullable=False)
    
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    driver = db.relationship('User', backref=db.backref('current_location', uselist=False))

    def to_dict(self):
        return {
            'driver_id': self.driver_id,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'updated_at': self.updated_at.isoformat()
        }

class ChatMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ride_id = db.Column(db.Integer, db.ForeignKey('ride.id'), nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    sender = db.relationship('User', foreign_keys=[sender_id], backref=db.backref('sent_messages', lazy='dynamic'))
    receiver = db.relationship('User', foreign_keys=[receiver_id], backref=db.backref('received_messages', lazy='dynamic'))

    def to_dict(self):
        return {
            'id': self.id,
            'ride_id': self.ride_id,
            'sender_id': self.sender_id,
            'receiver_id': self.receiver_id,
            'sender_name': self.sender.full_name if self.sender else "System",
            'content': self.content,
            'timestamp': self.timestamp.isoformat()
        }

class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ride_id = db.Column(db.Integer, db.ForeignKey('ride.id'), nullable=False)
    reviewer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    reviewee_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    rating = db.Column(db.Integer, nullable=False) 
    comment = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    reviewer = db.relationship('User', foreign_keys=[reviewer_id], backref='reviews_given')
    reviewee = db.relationship('User', foreign_keys=[reviewee_id], backref='reviews_received')
    ride = db.relationship('Ride', backref='reviews')

    def to_dict(self):
        return {
            'id': self.id,
            'rating': self.rating,
            'comment': self.comment,
            'created_at': self.created_at.isoformat()
        }