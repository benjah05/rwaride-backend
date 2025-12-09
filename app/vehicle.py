from flask import Blueprint, request, jsonify
from app import db
from app.models import User, Vehicle
from flask_jwt_extended import jwt_required, get_jwt_identity

vehicle_bp = Blueprint('vehicle', __name__)

def is_driver(user):
    """Checks if the user has a 'driver' or 'both' role."""
    return user.role in ['driver', 'both']


# Register a new vehicle
@vehicle_bp.route('/', methods=['POST'])
@jwt_required()
def register_vehicle():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    if not user or not is_driver(user):
        return jsonify({"msg": "Unauthorized: Only drivers can register vehicles"}), 403

    data = request.get_json()
    
    license_plate = data.get('license_plate')
    seat_capacity = data.get('seat_capacity')
    
    if not license_plate or not seat_capacity:
        return jsonify({"msg": "Missing required fields: license_plate and seat_capacity"}), 400

    # Ensure license plate is unique across the platform
    if Vehicle.query.filter_by(license_plate=license_plate).first():
        return jsonify({"msg": "Vehicle with this license plate already exists"}), 409

    try:
        new_vehicle = Vehicle(
            owner_id=user.id,
            license_plate=license_plate,
            seat_capacity=seat_capacity,
            make=data.get('make'),
            model=data.get('model'),
            year=data.get('year'),
            color=data.get('color')
        )
        db.session.add(new_vehicle)
        db.session.commit()
        
        return jsonify({
            "msg": "Vehicle registered successfully",
            "id": new_vehicle.id,
            "license_plate": new_vehicle.license_plate
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"msg": "Database error during vehicle registration", "error": str(e)}), 500

# Get all vehicles owned by the current user
@vehicle_bp.route('/', methods=['GET'])
@jwt_required()
def get_user_vehicles():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user or not is_driver(user):
        return jsonify({"msg": "Unauthorized: Access restricted to drivers"}), 403

    vehicles = user.vehicles.all()
    
    vehicle_list = []
    for vehicle in vehicles:
        vehicle_list.append({
            "id": vehicle.id,
            "license_plate": vehicle.license_plate,
            "make": vehicle.make,
            "model": vehicle.model,
            "year": vehicle.year,
            "color": vehicle.color,
            "seat_capacity": vehicle.seat_capacity,
            "is_verified": vehicle.is_verified
        })
        
    return jsonify(vehicle_list), 200

# Update a specific vehicle
@vehicle_bp.route('/<int:vehicle_id>', methods=['PUT'])
@jwt_required()
def update_vehicle(vehicle_id):
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    vehicle = Vehicle.query.get(vehicle_id)

    if not vehicle:
        return jsonify({"msg": "Vehicle not found"}), 404
        
    # Security Check: Ensure the user owns the vehicle
    if vehicle.owner_id != int(user_id):
        return jsonify({"msg": "Forbidden: You do not own this vehicle"}), 403

    data = request.get_json()
    
    if 'make' in data:
        vehicle.make = data['make']
    if 'model' in data:
        vehicle.model = data['model']
    if 'seat_capacity' in data:
        vehicle.seat_capacity = data['seat_capacity']
    if 'color' in data:
        vehicle.color = data['color']
    
    if 'license_plate' in data:
        vehicle.license_plate = data['license_plate']

    try:
        db.session.commit()
        return jsonify({"msg": "Vehicle updated successfully", "id": vehicle.id}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"msg": "Database error during update", "error": str(e)}), 500


# Delete a specific vehicle
@vehicle_bp.route('/<int:vehicle_id>', methods=['DELETE'])
@jwt_required()
def delete_vehicle(vehicle_id):
    user_id = get_jwt_identity()
    
    vehicle = Vehicle.query.get(vehicle_id)
    
    if not vehicle:
        return jsonify({"msg": "Vehicle not found"}), 404
        
    # Security Check: Ensure the user owns the vehicle
    if vehicle.owner_id != int(user_id):
        return jsonify({"msg": "Forbidden: You do not own this vehicle"}), 403

    try:
        db.session.delete(vehicle)
        db.session.commit()
        return jsonify({"msg": "Vehicle deleted successfully", "id": vehicle_id}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"msg": "Database error during deletion", "error": str(e)}), 500