from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_cors import CORS
from config import config
from flask_mail import Mail

from datetime import datetime
from app.tasks.cleanup import init_scheduler

db = SQLAlchemy()
migrate = Migrate()
mail = Mail()  # Initialize Flask-Mail
login_manager = LoginManager()

def create_app(config_name='development'):
    """Application factory"""
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(config[config_name])
    mail.init_app(app)  # Initialize Flask-Mail with the app

    @app.context_processor
    def inject_current_year():
        return {"current_year": datetime.now().year}
    
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    
    # Login manager config
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    
    # Register blueprints
    from app.main import main_bp
    from app.auth import auth_bp
    from app.bookings import bookings_bp
    from app.services import services_bp
    from app.admin import admin_bp
    from app.api import api_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(bookings_bp, url_prefix='/bookings')
    app.register_blueprint(services_bp, url_prefix='/services')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(api_bp, url_prefix='/api')
    
    # Create tables
    with app.app_context():
        db.create_all()
        init_scheduler(app)      # ← Add this line
    
    return app
