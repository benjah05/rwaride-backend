from flask import Blueprint, jsonify
from app.models import DriverLocation
from flask_jwt_extended import jwt_required

tracking_bp = Blueprint('tracking', __name__)

@tracking_bp.route('/location/<int:driver_id>', methods=['GET'])
@jwt_required()
def get_driver_location(driver_id):
    """
    Fetches the last known location of a driver.
    Useful for initializing the map view before live updates begin.
    """
    location = DriverLocation.query.filter_by(driver_id=driver_id).first()
    if not location:
        return jsonify({"msg": "No location data available for this driver."}), 404
        
    return jsonify(location.to_dict()), 200