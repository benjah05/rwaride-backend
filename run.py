from app import create_app, socketio

flask_app = create_app()

if __name__ == '__main__':
    socketio.run(flask_app, debug=False, use_reloader=False)