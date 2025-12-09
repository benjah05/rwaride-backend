from flask import Blueprint, request, jsonify
from app import db
from app.models import User
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required
from sqlalchemy import text 

auth_bp = Blueprint('auth', __name__)

VALID_ROLES = ['driver', 'passenger', 'both', 'admin']

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()

    full_name = data.get('full_name')
    phone = data.get('phone_number')
    password = data.get('password')
    email = data.get('email')
    
    raw_role = data.get('role')      
    driver_license_id = data.get('driver_license_id')

    if not password or not email or not full_name or not phone:
        return jsonify({"msg": "Missing required fields (full_name, email, phone_number, password)"}), 400

    role_map = {
        'Passenger': 'passenger', 'passenger': 'passenger',
        'Driver': 'driver', 'driver': 'driver', 'both': 'both',
        'Both Passenger & Driver': 'both', 'both passenger & driver': 'both',
        'Admin': 'admin',
        'admin': 'admin'
    }
    
    role = role_map.get(raw_role)
    
    if not role:
        return jsonify({"msg": "Invalid role selected"}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({"msg": "Email already registered"}), 400

    new_user = User(
        full_name=full_name,
        email=email,
        phone_number=phone,
        role=role,
        driver_license_id=driver_license_id if role in ['driver', 'both'] else None
    )
    new_user.set_password(password)

    try:
        db.session.add(new_user)
        db.session.commit()
        return jsonify({"msg": "User created successfully"}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"msg": "Database error", "error": str(e)}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()

    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({"msg": "Email and Password are required"}), 400

    user = User.query.filter_by(email=email).first()

    if user and user.check_password(password):
        access_token = create_access_token(identity=str(user.id))
        
        return jsonify({
            "msg": "Login successful",
            "access_token": access_token,
            "user": {
                "id": user.id,
                "full_name": user.full_name,
                "role": user.role,
                "email": user.email,
                "average_rating": user.average_rating,
                "is_identity_verified": user.is_identity_verified
            }
        }), 200
    
    return jsonify({"msg": "Invalid email or password"}), 401

@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    current_user_id = get_jwt_identity()
    
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({"msg": "User not found"}), 404

    return jsonify({
        "id": user.id,
        "phone_number": user.phone_number,
        "email": user.email,
        "full_name": user.full_name,
        "role": user.role,
        "bio": user.bio,
        "created_at": user.created_at,
        "average_rating": user.average_rating,
        "total_ride_count": user.total_ride_count,
        "is_identity_verified": user.is_identity_verified,
        "driver_license_id": user.driver_license_id,
        "is_license_verified": user.is_license_verified
    }), 200

@auth_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_user_profile():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    data = request.get_json()
    
    if not user:
        return jsonify({"msg": "User not found"}), 404
    
    if 'full_name' in data:
        user.full_name = data['full_name']

    if 'bio' in data:
        user.bio = data['bio']
    
    if 'phone_number' in data:
        user.phone_number = data['phone_number']

    if 'driver_license_id' in data and user.role in ['driver', 'both']:
        user.driver_license_id = data['driver_license_id']

    if 'password' in data:
        user.set_password(data['password'])
    
    try:
        db.session.commit()
        return jsonify({"msg": "Profile updated successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"msg": "Update failed", "error": str(e)}), 500

#----------------------------------------------------   
@auth_bp.route('/admin/db-reset', methods=['POST'])
@jwt_required()
def reset_db_history():
    # SECURITY CHECK: Only allow this if authenticated (though it should be deleted ASAP)
    user_id = get_jwt_identity()
    user = User.query.get(int(user_id))

    if not user:
        return jsonify({"msg": "Unauthorized"}), 401
    
    try:
        # Execute raw SQL to drop the corrupt history table
        with db.engine.connect() as connection:
            connection.execute(text("DROP TABLE IF EXISTS alembic_version;"))
            connection.commit()
            
        return jsonify({
            "msg": "Database history table (alembic_version) successfully deleted.",
            "WARNING": "DELETE THIS ENDPOINT IMMEDIATELY AFTER USE."
        }), 200

    except Exception as e:
        # Catch if the table doesn't exist or another connection error occurs
        return jsonify({"msg": "Failed to drop table (check logs)", "error": str(e)}), 500
#--------------------------------------------------------

@auth_bp.route('/profile', methods=['DELETE'])
@jwt_required()
def delete_user_account():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({"msg": "User not found"}), 404

    db.session.delete(user)
    
    try:
        db.session.commit()
        return jsonify({"msg": "Account deleted successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"msg": "Deletion failed", "error": str(e)}), 500