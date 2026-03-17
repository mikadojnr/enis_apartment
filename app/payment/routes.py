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
    current_app.logger.info("PAYSTACK WEBHOOK RECEIVED")

    # Read raw payload ONCE – very important!
    raw_payload = request.get_data()
    current_app.logger.info(f"Payload length: {len(raw_payload)} bytes")

    # Log headers (for debugging)
    signature = request.headers.get('X-Paystack-Signature')
    current_app.logger.info(f"X-Paystack-Signature: {signature[:30] + '...' if signature else 'MISSING'}")

    # Quick early return for Paystack health check (they sometimes send empty POST)
    if not raw_payload:
        current_app.logger.info("Empty payload - likely health check")
        return jsonify({"status": "ok"}), 200

    # Verify signature
    if not verify_paystack_signature(raw_payload, signature):
        current_app.logger.warning("Signature verification FAILED")
        return jsonify({"status": "invalid signature"}), 200  # Paystack wants 200

    # Parse JSON safely
    try:
        event = json.loads(raw_payload)
        current_app.logger.info(f"Event type: {event.get('event')}")
    except json.JSONDecodeError as e:
        current_app.logger.error(f"JSON parse failed: {str(e)}")
        return jsonify({"status": "invalid json"}), 200

    # Ignore non-success events
    if event.get('event') != 'charge.success':
        current_app.logger.info(f"Ignored event: {event.get('event')}")
        return jsonify({"status": "ignored"}), 200

    data = event.get('data', {})
    reference = data.get('reference')
    amount = data.get('amount', 0) / 100
    metadata = data.get('metadata', {})
    booking_ref = metadata.get('booking_reference')

    if not booking_ref:
        current_app.logger.warning(f"No booking_reference in metadata for ref: {reference}")
        return jsonify({"status": "no metadata"}), 200

    booking = Booking.query.filter_by(booking_reference=booking_ref).first()
    if not booking:
        current_app.logger.warning(f"Booking not found: {booking_ref}")
        return jsonify({"status": "booking not found"}), 200

    if booking.status != 'pending':
        current_app.logger.info(f"Booking already {booking.status} - skipping")
        return jsonify({"status": "already processed"}), 200

    # Create payment record
    payment = Payment(
        booking_id=booking.id,
        payment_reference=reference,
        amount=amount,
        currency=data.get('currency', 'NGN'),
        status='success',
        payment_method=data.get('channel', 'card'),
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

    current_app.logger.info(f"BOOKING CONFIRMED VIA WEBHOOK → {booking_ref} (ref: {reference})")

    return jsonify({"status": "success"}), 200