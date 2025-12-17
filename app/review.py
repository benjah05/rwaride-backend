from flask import Blueprint, request, jsonify
from app import db
from app.models import User, Review
from flask_jwt_extended import jwt_required, get_jwt_identity

review_bp = Blueprint('review', __name__)

# --- REVIEW ENDPOINTS ---

@review_bp.route('/submit', methods=['POST'])
@jwt_required()
def submit_review():
    user_id = get_jwt_identity()
    data = request.get_json()
    
    # Validation
    if not all(key in data for key in ['ride_id', 'reviewee_id', 'rating']):
        return jsonify({"msg": "Missing required fields"}), 400

    new_review = Review(
        ride_id=data['ride_id'],
        reviewer_id=user_id,
        reviewee_id=data['reviewee_id'],
        rating=data['rating'],
        comment=data.get('comment')
    )
    
    # Update average rating of the reviewee
    reviewee = User.query.get(data['reviewee_id'])
    if reviewee:
        all_reviews = Review.query.filter_by(reviewee_id=reviewee.id).all()
        current_total = sum([r.rating for r in all_reviews])
        count = len(all_reviews)
        reviewee.average_rating = (current_total + data['rating']) / (count + 1)
    
    db.session.add(new_review)
    db.session.commit()
    return jsonify({"msg": "Review submitted successfully"}), 201