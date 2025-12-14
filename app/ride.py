from flask import Blueprint, request, jsonify
from app import db
from app.models import User, Ride, Vehicle, PassengerRide
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timezone 
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError


ride_bp = Blueprint('ride', __name__) 

def is_driver(user):
    """Checks if the user has a 'driver' or 'both' role."""
    return user and user.role in ['driver', 'both']

# Driver Routes (Trip Management)

# Create a new ride offering
@ride_bp.route('/', methods=['POST'])
@jwt_required()
def create_ride():
    user_id = get_jwt_identity()
    user = User.query.get(int(user_id))

    if not is_driver(user):
        return jsonify({"msg": "Unauthorized: Only drivers can create rides"}), 403

    data = request.get_json()
    
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
        elif 'Z' in departure_time_str:
            departure_time_str = departure_time_str.replace('Z', '')
            
        departure_time = datetime.fromisoformat(departure_time_str)
        
    except (ValueError, TypeError) as e:
         return jsonify({"msg": f"Invalid data type or format. Error: {str(e)}"}), 400

    vehicle = Vehicle.query.get(vehicle_id)
    if not vehicle or vehicle.owner_id != user.id:
        return jsonify({"msg": "Invalid vehicle ID or vehicle not owned by user."}), 400
    
    if total_seats > vehicle.seat_capacity:
        return jsonify({"msg": f"Requested seats ({total_seats}) exceed vehicle capacity ({vehicle.seat_capacity})."}), 400
    
    if departure_time < datetime.now(timezone.utc).replace(tzinfo=None):
        return jsonify({"msg": "Cannot schedule a ride in the past."}), 400

    try:
        new_ride = Ride(
            driver_id=user.id,
            vehicle_id=vehicle_id,
            origin=data.get('origin'),
            destination=data.get('destination'),
            departure_time=departure_time,
            total_seats=total_seats,
            available_seats=total_seats, 
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
        return jsonify({"msg": "Database error during ride creation. Check server logs."}), 500

# Update Trip: Modify price, time, seats
@ride_bp.route('/<int:ride_id>', methods=['PUT'])
@jwt_required()
def update_ride(ride_id):
    driver_id = get_jwt_identity()
    ride = Ride.query.get(ride_id)

    if not ride:
        return jsonify({"msg": "Ride not found."}), 404
        
    if ride.driver_id != int(driver_id):
        return jsonify({"msg": "Forbidden: You are not the driver of this ride."}), 403

    if ride.status not in ['open', 'full']:
        return jsonify({"msg": f"Cannot update ride with status '{ride.status}'."}), 400
    
    data = request.get_json()

    try:
        # Update departure time
        if 'departure_time' in data:
            departure_time_str = data['departure_time']
            if '+' in departure_time_str:
                departure_time_str = departure_time_str.split('+')[0]
            elif 'Z' in departure_time_str:
                departure_time_str = departure_time_str.replace('Z', '')
            
            ride.departure_time = datetime.fromisoformat(departure_time_str)
            
        # Update seat capacity (handle logic if total seats decreases)
        if 'total_seats' in data:
            new_total_seats = int(data['total_seats'])
            if new_total_seats < ride.total_seats:
                # If capacity is reduced, ensure it doesn't drop below current bookings
                occupied_seats = ride.total_seats - ride.available_seats
                if new_total_seats < occupied_seats:
                    return jsonify({"msg": f"Cannot reduce total seats below {occupied_seats} (currently booked)."}), 400
                
                # Adjust available seats based on the reduction
                ride.available_seats -= (ride.total_seats - new_total_seats)

            elif new_total_seats > ride.total_seats:
                # If capacity increases, increase available seats
                ride.available_seats += (new_total_seats - ride.total_seats)
            
            ride.total_seats = new_total_seats
            # Ensure status is 'open' if seats become available
            if ride.available_seats > 0:
                ride.status = 'open'

        # Update other fields
        if 'origin' in data: ride.origin = data['origin']
        if 'destination' in data: ride.destination = data['destination']
        if 'vehicle_id' in data: ride.vehicle_id = int(data['vehicle_id'])

        db.session.commit()
        return jsonify({"msg": "Ride updated successfully", "id": ride.id}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"msg": "Database error during ride update", "error": str(e)}), 500

# Delete/Cancel Trip
@ride_bp.route('/<int:ride_id>', methods=['DELETE'])
@jwt_required()
def delete_ride(ride_id):
    driver_id = get_jwt_identity()
    ride = Ride.query.get(ride_id)

    if not ride:
        return jsonify({"msg": "Ride not found."}), 404
        
    if ride.driver_id != int(driver_id):
        return jsonify({"msg": "Forbidden: You are not the driver of this ride."}), 403
    
    active_bookings = PassengerRide.query.filter_by(
        ride_id=ride.id
    ).filter(
        PassengerRide.status.in_(['pending', 'confirmed'])
    ).all() # Fetch all active bookings

    if active_bookings:
        # If active bookings exist, only cancel the trip, don't delete the record
        ride.status = 'cancelled'
        for booking in active_bookings:
            booking.status = 'canceled'
        
        db.session.commit()
        return jsonify({"msg": f"Ride status changed to 'cancelled'. {len(active_bookings)} active booking(s) canceled."}), 200
    
    try:
        # Delete all associated PassengerRide records (even if cancelled)
        # This handles the integrity constraint.
        PassengerRide.query.filter_by(ride_id=ride.id).delete()
        
        # Delete the parent Ride record
        db.session.delete(ride)
        db.session.commit()
        return jsonify({"msg": "Ride and all associated bookings deleted successfully."}), 200
    
    except Exception as e:
        db.session.rollback()
        print(f"Ride deletion failed for ride {ride_id}: {str(e)}")
        return jsonify({"msg": "Database error during ride deletion. Check server logs."}), 500
    
# Get all rides posted by the current driver
@ride_bp.route('/driver', methods=['GET'])
@jwt_required()
def get_driver_rides():
    user_id = get_jwt_identity()
    
    # Includes logic to fetch associated bookings for history/oversight
    rides = Ride.query.filter_by(driver_id=int(user_id)).order_by(Ride.departure_time.desc()).all()
    
    ride_list = []
    for ride in rides:
        ride_dict = ride.to_dict()
        
        # Fetch bookings for this ride (7.5 Booking List for Driver)
        bookings = PassengerRide.query.filter_by(ride_id=ride.id).all()
        ride_dict['bookings'] = [{
            'booking_id': b.id,
            'passenger_id': b.passenger_id,
            'seats_booked': b.seats_booked,
            'status': b.status
        } for b in bookings]
        
        ride_list.append(ride_dict)

    return jsonify(ride_list), 200


# --- Passenger Routes ---

# Find open rides
@ride_bp.route('/search', methods=['GET'])
def search_rides():
    # Query parameters: ?origin=Kimironko&destination=Kacyiru
    origin_query = request.args.get('origin')
    destination_query = request.args.get('destination')
    
    query = Ride.query.filter_by(status='open')
    
    if origin_query:
        query = query.filter(Ride.origin.ilike(f'%{origin_query}%'))
        
    if destination_query:
        query = query.filter(Ride.destination.ilike(f'%{destination_query}%'))

    # Filter out rides happening in the past
    query = query.filter(Ride.departure_time > datetime.now(timezone.utc).replace(tzinfo=None))

    rides = query.order_by(Ride.departure_time.asc()).all()
    
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
    seats_requested = data.get('seats', 1) 

    if not isinstance(seats_requested, int) or seats_requested < 1:
        return jsonify({"msg": "Invalid number of seats requested."}), 400

    ride = Ride.query.get(ride_id)

    if not ride: return jsonify({"msg": "Ride not found."}), 404
    if ride.status != 'open': return jsonify({"msg": "Ride is not available for booking."}), 400
    if ride.driver_id == user.id: return jsonify({"msg": "Cannot book a seat on your own ride."}), 400
    if seats_requested > ride.available_seats:
        return jsonify({"msg": f"Requested {seats_requested} seats, but only {ride.available_seats} available."}), 409
        
    existing_booking = PassengerRide.query.filter_by(
        passenger_id=user.id, ride_id=ride.id
    ).first()

    if existing_booking:
        return jsonify({"msg": "You already have a booking for this ride."}), 409

    try:
        new_booking = PassengerRide(
            passenger_id=user.id,
            ride_id=ride.id,
            seats_booked=seats_requested,
            status='pending'
        )
        db.session.add(new_booking)
        
        ride.available_seats -= seats_requested
        if ride.available_seats == 0:
            ride.status = 'full'

        db.session.commit()
        
        return jsonify({
            "msg": "Booking created successfully. Pending driver confirmation.",
            "booking_id": new_booking.id,
            "status": "pending" 
        }), 201

    except IntegrityError:
        db.session.rollback()
        return jsonify({"msg": "Integrity Error: Booking failed due to database constraint."}), 500
    except Exception as e:
        db.session.rollback()
        return jsonify({"msg": "Database error during booking creation.", "error": str(e)}), 500

# Driver confirms a pending booking
@ride_bp.route('/booking/<int:booking_id>/approve', methods=['PUT'])
@jwt_required()
def approve_booking(booking_id):
    driver_id = get_jwt_identity()
    
    booking = PassengerRide.query.get(booking_id)

    if not booking: return jsonify({"msg": "Booking not found."}), 404
        
    ride = Ride.query.get(booking.ride_id)

    if ride.driver_id != int(driver_id):
        return jsonify({"msg": "Forbidden: You are not the driver of this ride."}), 403

    if booking.status != 'pending':
        return jsonify({"msg": f"Booking status is already '{booking.status}'. Only 'pending' can be approved."}), 400

    try:
        booking.status = 'confirmed'
        db.session.commit()
        
        return jsonify({
            "msg": "Booking confirmed successfully.",
            "booking_id": booking.id,
            "new_status": booking.status
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"msg": "Database error during booking approval.", "error": str(e)}), 500

# Passenger cancels their own booking
@ride_bp.route('/booking/<int:booking_id>/cancel', methods=['PUT'])
@jwt_required()
def cancel_booking(booking_id):
    passenger_id = get_jwt_identity()
    
    booking = PassengerRide.query.get(booking_id)

    if not booking: return jsonify({"msg": "Booking not found."}), 404
        
    if booking.passenger_id != int(passenger_id):
        return jsonify({"msg": "Forbidden: You do not own this booking."}), 403

    if booking.status not in ['pending', 'confirmed']:
        return jsonify({"msg": f"Cannot cancel booking with status '{booking.status}'."}), 400
        
    ride = Ride.query.get(booking.ride_id)

    try:
        # Update the booking status
        booking.status = 'canceled'
        
        # Release the seats back to the ride
        ride.available_seats += booking.seats_booked
        ride.status = 'open' # Ensure ride is set back to open if it was full

        db.session.commit()
        
        # this would trigger a refund and driver notification
        return jsonify({
            "msg": "Booking cancelled successfully. Seats released.",
            "booking_id": booking.id,
            "new_status": booking.status
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"msg": "Database error during booking cancellation.", "error": str(e)}), 500

# Get all bookings for the current user
@ride_bp.route('/bookings', methods=['GET'])
@jwt_required()
def get_user_bookings():
    passenger_id = get_jwt_identity()
    
    # Fetch all bookings the current user has made
    bookings = PassengerRide.query.filter_by(passenger_id=int(passenger_id)).all()
    
    booking_list = []
    for booking in bookings:
        ride = Ride.query.get(booking.ride_id)
        driver = User.query.get(ride.driver_id)
        
        booking_list.append({
            'booking_id': booking.id,
            'ride_id': ride.id,
            'status': booking.status,
            'seats_booked': booking.seats_booked,
            'trip_details': {
                'origin': ride.origin,
                'destination': ride.destination,
                'departure_time': ride.departure_time.isoformat(),
                'driver_name': driver.full_name,
                'driver_rating': driver.average_rating,
            }
        })
        
    return jsonify(booking_list), 200