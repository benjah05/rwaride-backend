from flask_socketio import emit, join_room, leave_room
from flask import request
from app import socketio, db
from app.models import User, ChatMessage
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

@socketio.on('join_chat')
def on_join_chat(data):
    # Standard connection handling does not need the token inside the event
    ride_id = data.get('ride_id')
    if ride_id:
        join_room(f"chat_{ride_id}")

@socketio.on('send_message')
def handle_message(data):
    """
    Receives a message and broadcasts it. Auth is done via query parameter token.
    """
    # FIX: Get token from the query string passed in the curl request
    token = request.args.get('token')
    user_id = get_user_id(token)

    if not user_id:
        # Token is invalid or missing, reject the event
        return 
    
    ride_id = data.get('ride_id')
    content = data.get('content')
    
    if not ride_id or not content: return

    # Save message to database
    msg = ChatMessage(
        ride_id=ride_id, 
        sender_id=user_id, 
        content=content
    )
    db.session.add(msg)
    db.session.commit()
    
    # Broadcast message to everyone in the ride chat room
    emit('new_message', msg.to_dict(), room=f"chat_{ride_id}")