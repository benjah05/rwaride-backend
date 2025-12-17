from flask_socketio import emit, join_room
from flask import request
from app import socketio, db
from app.models import DriverLocation
import jwt as pyjwt
from flask import current_app

def get_user_id(token):
    try:
        secret = current_app.config.get('JWT_SECRET_KEY')
        payload = pyjwt.decode(token, secret, algorithms=["HS256"])
        return payload.get('sub') or payload.get('identity')
    except:
        return None

@socketio.on('join_tracking')
def on_join_tracking(data):
    ride_id = data.get('ride_id')
    if ride_id:
        join_room(f"tracking_{ride_id}")

@socketio.on('update_location')
def handle_location(data):
    token = request.args.get('token')
    user_id = get_user_id(token)
    if not user_id: return
    
    # Update or create location record in the database
    loc = DriverLocation.query.filter_by(driver_id=user_id).first()
    if not loc:
        loc = DriverLocation(driver_id=user_id, latitude=data['lat'], longitude=data['lng'])
        db.session.add(loc)
    else:
        loc.latitude = data['lat']
        loc.longitude = data['lng']
    
    db.session.commit()
    
    # Broadcast to passengers tracking this specific ride
    broadcast_data = {
        "driver_id": user_id,
        "lat": data['lat'],
        "lng": data['lng']
    }
    emit('location_received', broadcast_data, room=f"tracking_{data['ride_id']}")