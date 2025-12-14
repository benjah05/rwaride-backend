from flask import Blueprint, request, jsonify
from app import db
from app.models import User, Ride, Vehicle, PassengerRide
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timezone
from sqlalchemy import or_

ride_bp = Blueprint('ride', __name__)

def is_driver(user):
    """Checks if the user has a 'driver' or 'both' role."""
    return user and user.role in ['driver', 'both']

# Driver Routes

# Create a new ride offering
@ride_bp.route('/', methods=['POST'])
@jwt_required()
def create_ride():
    user_id = get_jwt_identity()
    user = User.query.get(int(user_id))

    if not is_driver(user):
        return jsonify({"msg": "Unauthorized: Only drivers can create rides"}), 403

    data = request.get_json()
    
    # Input validation
    required_fields = ['origin', 'destination', 'departure_time', 'total_seats', 'vehicle_id']
    if not all(data.get(field) for field in required_fields):
        return jsonify({"msg": "Missing required trip details."}), 400

    try:
        vehicle_id = int(data.get('vehicle_id'))
        total_seats = int(data.get('total_seats'))
        departure_time_str = data.get('departure_time')

        # Timezone Parsing
        if '+' in departure_time_str:
            departure_time_str = departure_time_str.split('+')[0]
        elif 'Z' in departure_time_str: # Also strip Z if it indicates UTC
            departure_time_str = departure_time_str.replace('Z', '')
            
        departure_time = datetime.fromisoformat(departure_time_str)

    except (ValueError, TypeError):
         return jsonify({"msg": "Invalid data type for vehicle_id, total_seats, or departure_time."}), 400

    # Vehicle Ownership and Capacity Check
    vehicle = Vehicle.query.get(vehicle_id)
    if not vehicle or vehicle.owner_id != user.id:
        return jsonify({"msg": "Invalid vehicle ID or vehicle not owned by user."}), 400
    
    if total_seats > vehicle.seat_capacity:
        return jsonify({"msg": f"Requested seats ({total_seats}) exceed vehicle capacity ({vehicle.seat_capacity})."}), 400

    if departure_time < datetime.now(timezone.utc):
        return jsonify({"msg": "Cannot schedule a ride in the past."}), 400

    try:
        new_ride = Ride(
            driver_id=user.id,
            vehicle_id=vehicle_id,
            origin=data.get('origin'),
            destination=data.get('destination'),
            departure_time=departure_time,
            total_seats=total_seats,
            available_seats=total_seats, # Initially, all seats are available
            status='open'
        )
        db.session.add(new_ride)
        db.session.commit()
        
        return jsonify({
            "msg": "Ride posted successfully",
            "id": new_ride.id,
            "route": f"{new_ride.origin} to {new_ride.destination}"
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"msg": "Database error during ride creation", "error": str(e)}), 500

# Get all rides posted by the current driver
@ride_bp.route('/driver', methods=['GET'])
@jwt_required()
def get_driver_rides():
    user_id = get_jwt_identity()
    
    rides = Ride.query.filter_by(driver_id=int(user_id)).order_by(Ride.departure_time.desc()).all()
    
    return jsonify([ride.to_dict() for ride in rides]), 200

#  Driver confirms a pending booking
@ride_bp.route('/booking/<int:booking_id>/approve', methods=['PUT'])
@jwt_required()
def approve_booking(booking_id):
    driver_id = get_jwt_identity()
    
    booking = PassengerRide.query.get(booking_id)

    if not booking:
        return jsonify({"msg": "Booking not found."}), 404
        
    ride = Ride.query.get(booking.ride_id)

    # Authorization Check: Must be the driver of the ride
    if ride.driver_id != int(driver_id):
        return jsonify({"msg": "Forbidden: You are not the driver of this ride."}), 403

    # Status Check: Only pending bookings can be approved
    if booking.status != 'pending':
        return jsonify({"msg": f"Booking status is already '{booking.status}'. Only 'pending' can be approved."}), 400

    try:
        # Update the booking status
        booking.status = 'confirmed'
        db.session.commit()
        
        # Trigger a notification to the passenger
        return jsonify({
            "msg": "Booking confirmed successfully.",
            "booking_id": booking.id,
            "new_status": booking.status
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"msg": "Database error during booking approval.", "error": str(e)}), 500

# Passenger Routes

# Find open rides
@ride_bp.route('/search', methods=['GET'])
def search_rides():
    # Query parameters: ?origin=Kimironko&destination=Kacyiru
    origin_query = request.args.get('origin')
    destination_query = request.args.get('destination')
    
    query = Ride.query.filter_by(status='open')
    
    # Filter by origin (partial match using ilike for case-insensitivity)
    if origin_query:
        query = query.filter(Ride.origin.ilike(f'%{origin_query}%'))
        
    # Filter by destination (partial match)
    if destination_query:
        query = query.filter(Ride.destination.ilike(f'%{destination_query}%'))

    # Filter out rides happening in the past (only show future rides)
    query = query.filter(Ride.departure_time > datetime.now(timezone.utc))

    # Get results, ordered by departure time
    rides = query.order_by(Ride.departure_time.asc()).all()
    
    # Format the output to include driver name (requires joining or separate lookup)
    ride_list = []
    for ride in rides:
        driver = User.query.get(ride.driver_id)
        
        ride_data = ride.to_dict()
        ride_data['driver_name'] = driver.full_name
        ride_data['driver_rating'] = driver.average_rating
        
        ride_list.append(ride_data)
        
    return jsonify(ride_list), 200

# Create a new booking
@ride_bp.route('/<int:ride_id>/book', methods=['POST'])
@jwt_required()
def create_booking(ride_id):
    passenger_id = get_jwt_identity()
    user = User.query.get(int(passenger_id))

    data = request.get_json()
    seats_requested = data.get('seats', 1) # Default to 1 seat

    if not isinstance(seats_requested, int) or seats_requested < 1:
        return jsonify({"msg": "Invalid number of seats requested."}), 400

    ride = Ride.query.get(ride_id)

    if not ride:
        return jsonify({"msg": "Ride not found."}), 404
        
    if ride.status != 'open':
        return jsonify({"msg": "Ride is not available for booking."}), 400

    # Check if the passenger is the driver of this ride
    if ride.driver_id == user.id:
        return jsonify({"msg": "Cannot book a seat on your own ride."}), 400

    # Check if enough seats are available
    if seats_requested > ride.available_seats:
        return jsonify({
            "msg": f"Requested {seats_requested} seats, but only {ride.available_seats} available."
        }), 409
        
    # Check if passenger already has a booking for this ride (via UniqueConstraint)
    existing_booking = PassengerRide.query.filter_by(
        passenger_id=user.id,
        ride_id=ride.id
    ).first()

    if existing_booking:
        return jsonify({"msg": "You already have a booking for this ride."}), 409

    try:
        # Create the booking record
        new_booking = PassengerRide(
            passenger_id=user.id,
            ride_id=ride.id,
            seats_booked=seats_requested,
            status='pending' # Initial status before payment/confirmation
        )
        db.session.add(new_booking)
        
        # Reduce seat count and update ride status
        ride.available_seats -= seats_requested
        if ride.available_seats == 0:
            ride.status = 'full'

        db.session.commit()
        
        return jsonify({
            "msg": "Booking created successfully. Pending driver confirmation.",
            "booking_id": new_booking.id,
            "ride_id": ride.id,
            "seats_booked": seats_requested,
            "status": "pending" 
        }), 201

    except Exception as e:
        db.session.rollback()
        # In case of a rare database concurrency error, log and return 500
        return jsonify({"msg": "Database error during booking creation", "error": str(e)}), 500