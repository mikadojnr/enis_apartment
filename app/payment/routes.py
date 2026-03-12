# app/payments/routes.py
from datetime import datetime
from flask import Blueprint, request, jsonify, current_app
from app import db
from app.models import Booking, Payment
from app.bookings.routes import send_booking_confirmed_email
import hmac
import hashlib
import json
from app.payment import payments_bp

def get_paystack_secret():
    """Helper to safely get secret key from config"""
    secret = current_app.config.get('PAYSTACK_SECRET_KEY')
    if not secret:
        current_app.logger.error("PAYSTACK_SECRET_KEY not set in config!")
    return secret


def verify_paystack_signature(payload: bytes, signature: str) -> bool:
    """Verify Paystack webhook signature using HMAC-SHA512"""
    if not signature or not payload:
        return False

    secret_key = get_paystack_secret()
    if not secret_key:
        current_app.logger.error("Cannot verify signature — secret key missing")
        return False

    expected = 'sha512=' + hmac.new(
        secret_key.encode('utf-8'),
        payload,
        hashlib.sha512
    ).hexdigest()

    is_valid = hmac.compare_digest(expected, signature)
    if not is_valid:
        current_app.logger.warning(f"Signature mismatch. Expected: {expected[:20]}..., Received: {signature[:20]}...")
    return is_valid


@payments_bp.route('/paystack/webhook', methods=['POST'])
def paystack_webhook():
    """
    Paystack webhook endpoint (must return 200 even for ignored events)
    """
    # Get raw bytes — NEVER parse JSON before signature check!
    payload = request.get_data()
    signature = request.headers.get('X-Paystack-Signature')

    # Debug logging — very useful when troubleshooting 401
    current_app.logger.info("Paystack webhook received")
    current_app.logger.info(f"  Headers present: {list(request.headers.keys())}")
    current_app.logger.info(f"  X-Paystack-Signature present: {bool(signature)}")
    current_app.logger.info(f"  Payload length: {len(payload)} bytes")
    secret_prefix = get_paystack_secret()[:8] + '...' if get_paystack_secret() else 'NOT SET'
    current_app.logger.info(f"  Paystack secret key (first 8 chars): {secret_prefix}")

    if not signature:
        current_app.logger.warning("Webhook called without X-Paystack-Signature header")
        return jsonify({"status": "missing signature"}), 401

    # Verify signature — security critical
    if not verify_paystack_signature(payload, signature):
        current_app.logger.warning("Invalid Paystack webhook signature")
        return jsonify({"status": "invalid signature"}), 401

    try:
        event = json.loads(payload)
    except json.JSONDecodeError:
        current_app.logger.error("Invalid JSON in Paystack webhook payload")
        return jsonify({"status": "invalid json"}), 400

    # Paystack requires 200 OK for all non-error responses
    if event.get('event') != 'charge.success':
        current_app.logger.info(f"Ignored non-charge.success event: {event.get('event')}")
        return jsonify({"status": "ignored"}), 200

    data = event.get('data', {})
    reference = data.get('reference')
    amount_kobo = data.get('amount', 0)
    amount = amount_kobo / 100.0
    status = data.get('status')
    paid_at = data.get('paid_at')

    if status != 'success':
        current_app.logger.info(f"Ignored unsuccessful charge: {status}")
        return jsonify({"status": "not successful"}), 200

    # Try to find existing payment record
    payment = Payment.query.filter_by(payment_reference=reference).first()

    if payment:
        # Already processed — just update if needed
        if payment.status != 'success':
            payment.status = 'success'
            payment.gateway_response = json.dumps(data)
            payment.transaction_date = datetime.utcnow()
            db.session.commit()
            current_app.logger.info(f"Updated existing payment: {reference}")
    else:
        # New payment — try to match via metadata
        metadata = data.get('metadata', {})
        booking_ref = metadata.get('booking_reference')

        if not booking_ref:
            current_app.logger.warning(f"No booking_reference in metadata for ref: {reference}")
            return jsonify({"status": "no booking reference"}), 200

        booking = Booking.query.filter_by(booking_reference=booking_ref).first()
        if not booking or booking.status != 'pending':
            current_app.logger.warning(f"Booking not found or not pending: {booking_ref}")
            return jsonify({"status": "booking not payable"}), 200

        # Create payment record
        payment = Payment(
            booking_id=booking.id,
            payment_reference=reference,
            amount=amount,
            status='success',
            payment_method=data.get('channel', 'unknown'),
            gateway_response=json.dumps(data),
            transaction_date=datetime.utcnow()
        )
        db.session.add(payment)

        # Confirm booking
        booking.status = 'confirmed'
        booking.paid = True
        booking.expires_at = None
        db.session.commit()

        # Send confirmation email
        send_booking_confirmed_email(booking)

        current_app.logger.info(f"Payment confirmed via webhook for booking {booking_ref}")

    return jsonify({"status": "success"}), 200