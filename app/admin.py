from flask import Blueprint, request, jsonify
from app import db
from app.models import User, Ride, Vehicle
from app.decorators import admin_required
from flask_jwt_extended import jwt_required, get_jwt_identity

admin_bp = Blueprint('admin', __name__)

# --- ADMIN ENDPOINTS ---

@admin_bp.route('/stats', methods=['GET'])
@admin_required()
@jwt_required()
def get_stats():
    # In a real app, you would add a check here to ensure get_jwt_identity() is an admin
    stats = {
        "total_users": User.query.count(),
        "total_rides": Ride.query.count(),
        "pending_vehicles": Vehicle.query.filter_by(is_verified=False).count()
    }
    return jsonify(stats), 200

@admin_bp.route('/verify-vehicle/<int:vid>', methods=['POST'])
@admin_required()
@jwt_required()
def verify_vehicle(vid):
    # In a real app, you would add a check here to ensure get_jwt_identity() is an admin
    v = Vehicle.query.get(vid)
    if not v:
        return jsonify({"msg": "Vehicle not found"}), 404
        
    v.is_verified = True
    db.session.commit()
    return jsonify({"msg": f"Vehicle {v.license_plate} verified successfully"}), 200