# app/payments/__init__.py
from flask import Blueprint

payments_bp = Blueprint('payment', __name__, url_prefix='/payments')

from app.payment import routes  