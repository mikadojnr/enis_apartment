from flask import Blueprint, json, request, jsonify, current_app, url_for
from flask import render_template_string
from flask_login import current_user  # only if needed
from app import db, mail
from app.models import Booking, Payment
from app.bookings.routes import send_booking_confirmed_email
import requests
from datetime import datetime
from app.payment import payments_bp


PAYSTACK_VERIFY_URL = "https://api.paystack.co/transaction/verify/"


@payments_bp.route('/verify', methods=['POST'])
def verify_payment():
         
    """
    Called by frontend after Paystack popup success.
    Verifies transaction with Paystack API (most secure source).
    Updates booking + creates payment record + sends email.
    """

    PAYSTACK_SECRET_KEY = current_app.config.get('PAYSTACK_SECRET_KEY')
    if not PAYSTACK_SECRET_KEY:
        current_app.logger.error("PAYSTACK_SECRET_KEY is not set in config!")
   
    data = request.get_json()
    reference = data.get('reference')

    if not reference:
        current_app.logger.warning("Verify called without reference")
        return jsonify({"success": False, "message": "No reference provided"}), 400

    # ── Call Paystack Verify API ────────────────────────────────────────
    headers = {
        "Authorization": f"Bearer {PAYSTACK_SECRET_KEY}",
        "Content-Type": "application/json"
    }

    try:
        resp = requests.get(f"{PAYSTACK_VERIFY_URL}{reference}", headers=headers, timeout=10)
        resp.raise_for_status()
        result = resp.json()
    except requests.RequestException as e:
        current_app.logger.error(f"Paystack verify request failed: {e}")
        return jsonify({"success": False, "message": "Payment verification service unavailable"}), 503

    if not result.get("status"):
        current_app.logger.warning(f"Paystack verify failed: {result}")
        return jsonify({
            "success": False,
            "message": result.get("message", "Verification failed")
        }), 400

    paystack_data = result["data"]
    if paystack_data["status"] != "success":
        return jsonify({
            "success": False,
            "message": f"Payment not successful: {paystack_data['status']}"
        }), 400

    # Trusted data from Paystack
    amount_paid = paystack_data["amount"] / 100.0  # convert kobo to Naira
    email = paystack_data["customer"]["email"]
    channel = paystack_data.get("channel", "unknown")

    # Try to find booking — use metadata if available
    metadata = paystack_data.get("metadata", {})
    booking_ref = metadata.get("booking_reference") or reference  # fallback to ref

    booking = Booking.query.filter_by(booking_reference=booking_ref).first()

    if not booking:
        current_app.logger.warning(f"No booking found for reference/metadata: {booking_ref}")
        return jsonify({"success": False, "message": "No matching booking found"}), 404

    if booking.status != "pending":
        current_app.logger.info(f"Booking {booking_ref} already processed (status: {booking.status})")
        return jsonify({
            "success": True,
            "message": f"Booking already {booking.status}",
            "booking_status": booking.status
        })

    # ── Create or update payment record ────────────────────────────────
    payment = Payment.query.filter_by(payment_reference=reference).first()

    if not payment:
        payment = Payment(
            booking_id=booking.id,
            payment_reference=reference,
            amount=amount_paid,
            status="success",
            payment_method=channel,
            gateway_response=json.dumps(paystack_data),
            transaction_date=datetime.utcnow()
        )
        db.session.add(payment)
    else:
        # Rare case — update if needed
        payment.status = "success"
        payment.amount = amount_paid
        payment.gateway_response = json.dumps(paystack_data)

    # ── Confirm booking ────────────────────────────────────────────────
    booking.status = "confirmed"
    booking.paid = True
    booking.expires_at = None

    db.session.commit()

    # Send confirmation email
    try:
        send_booking_confirmed_email(booking)
    except Exception as e:
        current_app.logger.error(f"Failed to send confirmation email: {e}")

    current_app.logger.info(f"Payment verified and booking confirmed: {booking.booking_reference}")

    return jsonify({
        "success": True,
        "message": "Payment verified and booking confirmed",
        "booking_reference": booking.booking_reference,
        "status": booking.status,
        "redirect_url": url_for('bookings.dashboard') if current_user.is_authenticated else 
                    url_for('bookings.guest_access', ref=booking.booking_reference)
    })