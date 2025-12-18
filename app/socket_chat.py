from flask_socketio import emit, join_room
from flask import request
from app import socketio, db
from app.models import User, ChatMessage
import jwt as pyjwt
from flask import current_app

def get_user_id(token):
    try:
        secret = current_app.config.get('JWT_SECRET_KEY')
        payload = pyjwt.decode(token, secret, algorithms=["HS256"])
        return payload.get('sub') or payload.get('identity')
    except:
        return None

@socketio.on('connect')
def handle_connect():
    token = request.args.get('token')
    user_id = get_user_id(token)
    if user_id:
        # Every user joins their own private room: "user_5"
        # This allows us to send direct messages to them
        join_room(f"user_{user_id}")

@socketio.on('join_ride_chat')
def on_join_ride(data):
    ride_id = data.get('ride_id')
    if ride_id:
        join_room(f"ride_{ride_id}")

@socketio.on('send_direct_message')
def handle_direct_message(data):
    """
    Sends a message to a specific person (e.g., Passenger to Driver).
    """
    token = request.args.get('token')
    sender_id = get_user_id(token)
    if not sender_id: return

    receiver_id = data.get('receiver_id')
    ride_id = data.get('ride_id')
    content = data.get('content')

    if not all([receiver_id, content]): return

    # Save to DB
    msg = ChatMessage(
        ride_id=ride_id,
        sender_id=sender_id,
        receiver_id=receiver_id, # You'll need to add this column to ChatMessage model
        content=content
    )
    db.session.add(msg)
    db.session.commit()

    # BROADCAST specifically to the receiver's private room
    # And to the sender's room (so it shows up on their other devices)
    payload = msg.to_dict()
    emit('new_private_message', payload, room=f"user_{receiver_id}")
    emit('new_private_message', payload, room=f"user_{sender_id}")

@socketio.on('send_ride_message')
def handle_ride_message(data):
    """
    Existing group chat logic for everyone in the ride.
    """
    token = request.args.get('token')
    sender_id = get_user_id(token)
    if not sender_id: return
    
    ride_id = data.get('ride_id')
    content = data.get('content')
    
    msg = ChatMessage(ride_id=ride_id, sender_id=sender_id, content=content)
    db.session.add(msg)
    db.session.commit()
    
    emit('new_ride_message', msg.to_dict(), room=f"ride_{ride_id}")