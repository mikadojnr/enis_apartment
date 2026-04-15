from flask import Blueprint, json, request, jsonify, current_app, url_for
from flask import render_template_string
from flask_login import current_user  # only if needed
from app import db, mail
from app.models import Booking, Payment, ServiceRequest
from app.bookings.routes import send_booking_confirmed_email, send_new_service_request_email, send_service_request_confirmation_email
import requests
from datetime import datetime
from app.payment import payments_bp


PAYSTACK_VERIFY_URL = "https://api.paystack.co/transaction/verify/"

@payments_bp.route('/verify', methods=['POST'])
def verify_payment():
    """Unified payment verification for both Bookings and Service Requests"""
    
    PAYSTACK_SECRET_KEY = current_app.config.get('PAYSTACK_SECRET_KEY')
    if not PAYSTACK_SECRET_KEY:
        current_app.logger.error("PAYSTACK_SECRET_KEY is not set in config!")
        return jsonify({"success": False, "message": "Payment configuration error"}), 500

    data = request.get_json()
    reference = data.get('reference')

    if not reference:
        return jsonify({"success": False, "message": "No reference provided"}), 400

    # Verify with Paystack
    headers = {
        "Authorization": f"Bearer {PAYSTACK_SECRET_KEY}",
        "Content-Type": "application/json"
    }

    try:
        resp = requests.get(f"{PAYSTACK_VERIFY_URL}{reference}", headers=headers, timeout=15)
        resp.raise_for_status()
        result = resp.json()
    except requests.RequestException as e:
        current_app.logger.error(f"Paystack verify failed: {e}")
        return jsonify({"success": False, "message": "Unable to verify payment with gateway"}), 503

    if not result.get("status") or result["data"]["status"] != "success":
        return jsonify({
            "success": False,
            "message": result.get("message", "Payment verification failed")
        }), 400

    paystack_data = result["data"]
    amount_paid = paystack_data["amount"] / 100.0
    metadata = paystack_data.get("metadata", {})
    payment_type = metadata.get("type", "booking")   # 'booking' or 'service_request'

    # ────────────────────────────────────────────────────────────────
    # HANDLE BOOKING PAYMENT
    # ────────────────────────────────────────────────────────────────
    if payment_type == "booking":
        booking_ref = metadata.get("booking_reference") or reference
        booking = Booking.query.filter_by(booking_reference=booking_ref).first()

        if not booking:
            return jsonify({"success": False, "message": "No matching booking found"}), 404

        if booking.status != "pending":
            return jsonify({
                "success": True,
                "message": f"Booking already {booking.status}",
                "booking_status": booking.status
            })

        # Create/Update Payment Record
        payment = Payment.query.filter_by(payment_reference=reference).first()
        if not payment:
            payment = Payment(
                booking_id=booking.id,
                payment_reference=reference,
                amount=amount_paid,
                currency='NGN',
                status='success',
                payment_method=paystack_data.get("channel", "paystack"),
                gateway_response=str(paystack_data),
                transaction_date=datetime.utcnow()
            )
            db.session.add(payment)

        # Confirm Booking
        booking.status = "confirmed"
        booking.paid = True
        booking.expires_at = None

        db.session.commit()
        send_booking_confirmed_email(booking)

        return jsonify({
            "success": True,
            "message": "Booking payment successful",
            "type": "booking",
            "booking_reference": booking.booking_reference,
            "redirect_url": url_for('bookings.dashboard') if current_user.is_authenticated else None
        })

    # ────────────────────────────────────────────────────────────────
    # HANDLE SERVICE REQUEST PAYMENT
    # ────────────────────────────────────────────────────────────────
    elif payment_type == "service_request":
        request_id = metadata.get("request_id")
        if not request_id:
            return jsonify({"success": False, "message": "Missing request_id in metadata"}), 400

        service_request = ServiceRequest.query.get(request_id)
        if not service_request:
            return jsonify({"success": False, "message": "Service request not found"}), 404

        if service_request.paid:
            return jsonify({"success": True, "message": "Service already paid"})

        existing_payment = Payment.query.filter_by(
            payment_reference=reference
        ).first()

        if existing_payment:
            # Already processed → just return success

            existing_payment.status = 'success'
            existing_payment.gateway_response = str(paystack_data)
            existing_payment.currency = str(paystack_data.get("currency"))
            existing_payment.transaction_date = datetime.now()

            db.session.commit()        

        # # Create Payment Record (linked to booking)
        # payment = Payment(
        #     booking_id=service_request.booking_id,
        #     payment_reference=reference,
        #     amount=amount_paid,
        #     currency='NGN',
        #     status='success',
        #     payment_method=paystack_data.get("channel", "paystack"),
        #     gateway_response=str(paystack_data),
        #     transaction_date=datetime.utcnow()
        # )
        # db.session.add(payment)

        # Mark Service Request as Paid
        service_request.paid = True
        service_request.paid_at = datetime.utcnow()
        # service_request.payment_reference = reference
        service_request.status = 'in_progress'  # Still waiting admin action on completion

        db.session.commit()

        # Send notifications
        send_new_service_request_email([service_request])
        send_service_request_confirmation_email([service_request])

        return jsonify({
            "success": True,
            "message": "Service payment successful",
            "type": "service_request",
            "request_id": service_request.id,
            "service_name": service_request.service.name,
            "booking_reference": service_request.booking.booking_reference
        })

    else:
        return jsonify({"success": False, "message": "Unknown payment type"}), 400