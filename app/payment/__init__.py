# app/payments/__init__.py
from flask import Blueprint

payments_bp = Blueprint('payment', __name__)

from app.payment import routes  