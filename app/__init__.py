import os
from dotenv import load_dotenv
from datetime import timedelta
from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_cors import CORS
from config import config
from flask_mail import Mail, Message
from flask_wtf.csrf import CSRFProtect

from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from datetime import datetime


limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

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
    
    # Ensure upload folder exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True) 
    

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
    # print("Flask-Mail Configuration Loaded:")
    # print(f"  MAIL_SERVER:         {app.config.get('MAIL_SERVER')}")
    # print(f"  MAIL_PORT:           {app.config.get('MAIL_PORT')}")
    # print(f"  MAIL_USE_TLS:        {app.config.get('MAIL_USE_TLS')}")
    # print(f"  MAIL_USERNAME:       {app.config.get('MAIL_USERNAME')}")
    # print(f"  MAIL_DEFAULT_SENDER: {app.config.get('MAIL_DEFAULT_SENDER')}")
    # print(f"  IDANALYZER_API_KEY:  {app.config.get('IDANALYZER_API_KEY')}")


    # 3. Initialize ALL extensions AFTER config is loaded
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    mail.init_app(app)         
    cors.init_app(app, resources={r"/api/*": {"origins": "*"}})
    csrf.init_app(app)          # Enable CSRF protection globally
    limiter.init_app(app)       # Initialize rate limiter

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
    from app.verification import verification_bp

   
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(bookings_bp, url_prefix='/bookings')
    app.register_blueprint(services_bp, url_prefix='/services')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(payments_bp, url_prefix='/payments')
    app.register_blueprint(verification_bp, url_prefix='/verify-id')

    # Context processor for current year
    @app.context_processor
    def inject_current_year():
        return {"current_year": datetime.now().year}

    
    # Your scheduler (keep this)
    from app.tasks.cleanup import init_scheduler

    with app.app_context():
        # db.create_all()
        init_scheduler(app)      # ← Add this line
    

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

        # ====================== ERROR HANDLERS ======================
    def error_handler(error_code, template, title, icon):
        def handler(e):
            return render_template(f'errors/{template}.html',
                                   error_code=error_code,
                                   title=title,
                                   message=e.description if hasattr(e, 'description') else "An error occurred.",
                                   icon=icon), error_code
        return handler

    # Register error handlers
    app.register_error_handler(404, error_handler(404, "404", "Page Not Found", '<i class="fa-solid fa-face-frown text-[#E96C40]"></i>'))
    app.register_error_handler(500, error_handler(500, "500", "Server Error", '<i class="fa-solid fa-tools text-red-500"></i>'))
    app.register_error_handler(403, error_handler(403, "403", "Access Denied", '<i class="fa-solid fa-lock text-amber-500"></i>'))
    app.register_error_handler(400, error_handler(400, "400", "Bad Request", '<i class="fa-solid fa-circle-exclamation text-red-500"></i>'))
    return app
