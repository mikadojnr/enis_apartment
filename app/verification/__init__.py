from flask import Blueprint

verification_bp = Blueprint('verification', __name__)

from app.verification import routes
