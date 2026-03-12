# config.py
import os
from datetime import timedelta
from dotenv import load_dotenv

# ────────────────────────────────────────────────
# Load .env file VERY EARLY — before ANY config class is defined
# This ensures os.environ has all values when classes are evaluated
# ────────────────────────────────────────────────
load_dotenv()

class Config:
    """Base configuration — shared by all environments"""
    # Flask basics
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'fallback-secret-key-do-not-use-in-prod'

    # Database
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_RECORD_QUERIES = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///eni_apartments.db'

    # Session security
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    SESSION_COOKIE_SECURE = True          # Enforce HTTPS in production
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'

    # WTForms / CSRF
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = None

    # Flask-Mail defaults (overridden by env vars)
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USE_SSL = False
    MAIL_USERNAME = None
    MAIL_PASSWORD = None
    MAIL_DEFAULT_SENDER = 'Eni\'s Apartments <enisapartment@gmail.com>'
    MAIL_DEBUG = 1  # Show SMTP conversation in console (dev only)

    # Paystack (loaded from .env or fallback to empty)
    PAYSTACK_SECRET_KEY = os.environ.get('PAYSTACK_SECRET_KEY')
    PAYSTACK_PUBLIC_KEY  = os.environ.get('PAYSTACK_PUBLIC_KEY')


class DevelopmentConfig(Config):
    """Development settings — more verbose, less secure"""
    DEBUG = True
    TESTING = False
    SQLALCHEMY_ECHO = True  # Show SQL queries in console

    # Force mail credentials from env (no fallback here)
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER') or Config.MAIL_DEFAULT_SENDER


class ProductionConfig(Config):
    """Production settings — secure, no debug output"""
    DEBUG = False
    TESTING = False
    SQLALCHEMY_ECHO = False

    # Enforce secure settings
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_SAMESITE = 'Strict'    # More secure in prod

    # Mail should use real credentials — no fallback
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER')


class TestingConfig(Config):
    """Testing / CI settings — fast, in-memory DB"""
    TESTING = True
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    SECRET_KEY = 'test-secret-key-for-ci-only'


# ────────────────────────────────────────────────
# Config mapping — used in create_app(config_name)
# ────────────────────────────────────────────────
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}