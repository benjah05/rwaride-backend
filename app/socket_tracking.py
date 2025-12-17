from flask_socketio import emit, join_room, leave_room
from flask import request
from app import socketio, db
from app.models import DriverLocation, User
import jwt as pyjwt
from flask import current_app

def get_user_id(token):
    """Helper to decode JWT and get user ID."""
    try:
        secret = current_app.config.get('JWT_SECRET_KEY')
        payload = pyjwt.decode(token, secret, algorithms=["HS256"])
        return payload.get('sub') or payload.get('identity')
    except:
        return None

@socketio.on('join_tracking')
def on_join_tracking(data):
    # This event is typically used by passengers
    ride_id = data.get('ride_id')
    if ride_id:
        join_room(f"tracking_{ride_id}")

@socketio.on('update_location')
def handle_location(data):
    """
    Driver calls this to update their GPS. Auth is done via query parameter token.
    """
    # FIX: Get token from the query string passed in the curl request
    token = request.args.get('token')
    user_id = get_user_id(token)
    
    if not user_id: 
        # Token is invalid or missing, reject the event
        return 

    user = User.query.get(user_id)
    if not user or user.role not in ['driver', 'both']:
        return # Only drivers can send location

    ride_id = data.get('ride_id')
    lat = data.get('lat')
    lng = data.get('lng')
    
    if not all([ride_id, lat, lng]): return

    # 1. Persistent Storage (Update or Create)
    loc = DriverLocation.query.filter_by(driver_id=user_id).first()
    if not loc:
        loc = DriverLocation(driver_id=user_id, latitude=lat, longitude=lng)
        db.session.add(loc)
    else:
        loc.latitude = lat
        loc.longitude = lng
    
    db.session.commit()
    
    # 2. BROADCAST to passengers in the room
    broadcast_data = {
        "driver_id": user_id,
        "lat": lat,
        "lng": lng,
        "ride_id": ride_id
    }
    emit('location_received', broadcast_data, room=f"tracking_{ride_id}")