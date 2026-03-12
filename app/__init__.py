import os
from dotenv import load_dotenv
from datetime import timedelta
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_cors import CORS
from config import config
from flask_mail import Mail, Message
from flask_wtf.csrf import CSRFProtect

from datetime import datetime
<<<<<<< HEAD
# from app.tasks.cleanup import init_scheduler
=======
from app.tasks.cleanup import init_scheduler
>>>>>>> 7bc39a227ea8df6f1021f33b0e25bbbb67c5c043

db = SQLAlchemy()
migrate = Migrate()
mail = Mail()  # Initialize Flask-Mail
login_manager = LoginManager()
cors = CORS()
csrf = CSRFProtect()

def create_app(config_name='development'):
    app = Flask(__name__)

    # 1. Load configuration FIRST
    app.config.from_object(config[config_name])

    # 2. Override/ensure mail settings from environment (after .env is loaded in config.py)
    # These are already pulled in DevelopmentConfig, but we reinforce here
    if 'MAIL_SERVER' in os.environ:
        app.config['MAIL_SERVER'] = os.environ['MAIL_SERVER']
    if 'MAIL_PORT' in os.environ:
        app.config['MAIL_PORT'] = int(os.environ['MAIL_PORT'])
    if 'MAIL_USE_TLS' in os.environ:
        app.config['MAIL_USE_TLS'] = os.environ['MAIL_USE_TLS'].lower() in ('true', '1', 'yes')
    if 'MAIL_USERNAME' in os.environ:
        app.config['MAIL_USERNAME'] = os.environ['MAIL_USERNAME']
    if 'MAIL_PASSWORD' in os.environ:
        app.config['MAIL_PASSWORD'] = os.environ['MAIL_PASSWORD']
    if 'MAIL_DEFAULT_SENDER' in os.environ:
        app.config['MAIL_DEFAULT_SENDER'] = os.environ['MAIL_DEFAULT_SENDER']

    # Debug print (very useful)
    print("Flask-Mail Configuration Loaded:")
    print(f"  MAIL_SERVER:         {app.config.get('MAIL_SERVER')}")
    print(f"  MAIL_PORT:           {app.config.get('MAIL_PORT')}")
    print(f"  MAIL_USE_TLS:        {app.config.get('MAIL_USE_TLS')}")
    print(f"  MAIL_USERNAME:       {app.config.get('MAIL_USERNAME')}")
    print(f"  MAIL_DEFAULT_SENDER: {app.config.get('MAIL_DEFAULT_SENDER')}")

    # 3. Initialize ALL extensions AFTER config is loaded
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    mail.init_app(app)          # MUST come after config — binds to app.extensions['mail']
    cors.init_app(app, resources={r"/api/*": {"origins": "*"}})
    csrf.init_app(app)          # Enable CSRF protection globally

    # Login manager settings
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
    from app.payment import payments_bp

   
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(bookings_bp, url_prefix='/bookings')
    app.register_blueprint(services_bp, url_prefix='/services')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(payments_bp)

    # Context processor for current year
    @app.context_processor
    def inject_current_year():
        return {"current_year": datetime.now().year}

    # Test route — now guaranteed to work if config is correct
    # @app.route('/test-email')
    # def test_email():
    #     try:
    #         msg = Message(
    #             subject="Test Email from Eni's Apartments",
    #             sender=app.config['MAIL_DEFAULT_SENDER'],
    #             recipients=["officialudobad@gmail.com"],
    #             body="Plain text test — Flask-Mail is working!",
    #             html="<h1>Test Success</h1><p>This is an HTML test email.</p>"
    #         )
    #         mail.send(msg)
    #         return "Test email sent! Check your inbox/spam folder."
    #     except Exception as e:
    #         import traceback
    #         error_detail = traceback.format_exc()
    #         print("Email send error:\n", error_detail)
    #         return f"<pre>Email failed:\n{str(e)}\n\nFull traceback:\n{error_detail}</pre>", 500

    # Your scheduler (keep this)
    with app.app_context():
<<<<<<< HEAD
        from app.tasks.cleanup import init_scheduler
        init_scheduler(app)

    return app
=======
        db.create_all()
        init_scheduler(app)      # ← Add this line
    
    return app
>>>>>>> 7bc39a227ea8df6f1021f33b0e25bbbb67c5c043
