from flask import Flask
from flask_cors import CORS  # Import CORS
from config import Config
from database import db
from routes import routes  # Import the blueprint directly
from flask_mail import Mail 
from flask_migrate import Migrate  # Import Migrate
from datetime import timedelta
from flask_jwt_extended import JWTManager  # Import JWT Manager

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Enable CORS for specified origins and methods
    CORS(app, resources={r"/*": {"origins": ["http://127.0.0.1:5000", "http://localhost:3000"],
                                  "methods": ["GET", "POST", "DELETE", "OPTIONS"],
                                  "supports_credentials": True}})

    # Set secret key and session cookie configurations
    app.config['SECRET_KEY'] = "3d1139f9a28f5d4b2b57e8ca2fd70d9e"
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=1)
    app.config['SESSION_COOKIE_SAMESITE'] = "None"  # Necessary for cross-site cookie sharing
    app.config['SESSION_COOKIE_SECURE'] = False  # Set to True in production

    # Initialize Mail for sending emails
    mail = Mail(app)

    # Initialize the database and migration
    db.init_app(app)
    migrate = Migrate(app, db)  # Initialize migrate with the app and db

    # Initialize JWT Manager
    jwt = JWTManager(app)  # Set up JWT manager

    # Register the blueprint for routes
    app.register_blueprint(routes)

    return app  # Return the created app instance

if __name__ == '__main__':
    app = create_app()  # Create an app instance
    app.run(debug=True)  # Run the app
