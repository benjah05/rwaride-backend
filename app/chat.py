from flask import Blueprint, jsonify
from app.models import ChatMessage, User
from flask_jwt_extended import jwt_required

chat_bp = Blueprint('chat', __name__)

@chat_bp.route('/history/<int:ride_id>', methods=['GET'])
@jwt_required()
def get_chat_history(ride_id):
    """
    Fetches all previous messages for a specific ride.
    Returns a list of messages including sender names for the UI to display.
    """
    # Query messages for this ride, ordered by time (oldest first)
    messages = ChatMessage.query.filter_by(ride_id=ride_id).order_by(ChatMessage.timestamp.asc()).all()
    
    # We use a list comprehension to convert all messages to dictionaries.
    # The to_dict() method in your models.py should include 'sender_name'.
    history = []
    for m in messages:
        msg_data = m.to_dict()
        # Ensure sender_name is present even if to_dict is minimal
        if 'sender_name' not in msg_data:
            msg_data['sender_name'] = m.sender.full_name
        history.append(msg_data)

    return jsonify(history), 200