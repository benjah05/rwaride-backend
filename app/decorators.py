from functools import wraps
from flask import jsonify
from flask_jwt_extended import get_jwt_identity
from app.models import User

def admin_required():
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            current_user_id = get_jwt_identity()
            user = User.query.get(current_user_id)
            
            # THE SECURITY CHECK
            if not user or user.role != 'admin':
                return jsonify({"msg": "Admins only!"}), 403
            
            return fn(*args, **kwargs)
        return decorator
    return wrapper