from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_socketio import SocketIO
from config import Config

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
socketio = SocketIO()

def create_app():
    flask_app = Flask(__name__)
    flask_app.config.from_object(Config)

    # Initialize plugins
    db.init_app(flask_app)
    migrate.init_app(flask_app, db)
    jwt.init_app(flask_app)
    CORS(flask_app) # Allow frontend to talk to this backend
    socketio.init_app(flask_app, cors_allowed_origins="*", async_mode=None)

    # Import and register Blueprints

    # Auth Routes
    from app.auth import auth_bp
    flask_app.register_blueprint(auth_bp, url_prefix='/api/auth')

    # Vehicle Registration
    from app.vehicle import vehicle_bp
    flask_app.register_blueprint(vehicle_bp, url_prefix='/api/vehicles')

    # Rides and Bookings Route
    from app.ride import ride_bp
    flask_app.register_blueprint(ride_bp, url_prefix='/api/rides')

    from app.admin import admin_bp
    flask_app.register_blueprint(admin_bp, url_prefix='/api/admin')

    from app.review import review_bp
    flask_app.register_blueprint(review_bp, url_prefix='/api/reviews')

    from app.chat import chat_bp
    flask_app.register_blueprint(chat_bp, url_prefix='/api/chat')

    from app.tracking import tracking_bp
    flask_app.register_blueprint(tracking_bp, url_prefix='/api/tracking')

    from app import socket_tracking, socket_chat

    return flask_app