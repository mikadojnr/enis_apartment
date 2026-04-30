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
        payment_reference = metadata.get("payment_reference")

        if not payment_reference:
            return jsonify({"success": False, "message": "Missing payment_reference"}), 400

        # 🔥 Get ALL requests tied to this payment
        service_requests = ServiceRequest.query.filter_by(
            payment_reference=payment_reference
        ).all()

        if not service_requests:
            return jsonify({"success": False, "message": "Service requests not found"}), 404

        # If already paid
        if all(req.paid for req in service_requests):
            return jsonify({"success": True, "message": "Services already paid"})

        # Update payment record
        payment = Payment.query.filter_by(
            payment_reference=reference
        ).first()

        if payment:
            payment.status = 'success'
            payment.gateway_response = str(paystack_data)
            payment.currency = str(paystack_data.get("currency"))
            payment.transaction_date = datetime.utcnow()

        # 🔥 Update ALL service requests
        for req in service_requests:
            req.paid = True
            req.paid_at = datetime.utcnow()
            req.status = 'in_progress'

        db.session.commit()

        # 🔥 Send ONE email with ALL services
        send_new_service_request_email(service_requests)
        send_service_request_confirmation_email(service_requests)

        return jsonify({
            "success": True,
            "message": "Service payment successful",
            "type": "service_request",
            "request_ids": [r.id for r in service_requests],
            "booking_reference": service_requests[0].booking.booking_reference
        })
    

    # ────────────────────────────────────────────────────────────────
    # HANDLE BOOKING EXTENSION PAYMENT
    # ────────────────────────────────────────────────────────────────
    elif payment_type == "extension":
        extension_id = metadata.get("extension_id")
        if not extension_id:
            return jsonify({"success": False, "message": "Missing extension_id"}), 400

        extension = BookingExtension.query.get(extension_id)
        if not extension:
            return jsonify({"success": False, "message": "Extension not found"}), 404

        if extension.paid:
            return jsonify({"success": True, "message": "Extension already paid"})

        # Create Payment record
        payment = Payment(
            booking_id=extension.booking_id,
            payment_reference=reference,
            amount=amount_paid,
            currency='NGN',
            status='success',
            payment_method=paystack_data.get("channel", "paystack"),
            gateway_response=str(paystack_data),
            transaction_date=datetime.utcnow()
        )
        db.session.add(payment)

        # Update Extension
        extension.paid = True
        extension.paid_at = datetime.utcnow()
        extension.payment_reference = reference
        extension.status = 'approved'          # Auto-approve after payment

        # Update original booking check-out date
        extension.booking.check_out_date = extension.new_check_out
        extension.booking.total_price += float(extension.extra_amount)

        db.session.commit()

        return jsonify({
            "success": True,
            "message": "Stay extension payment successful. Booking updated.",
            "type": "extension",
            "extension_id": extension.id,
            "new_check_out": extension.new_check_out.strftime('%Y-%m-%d'),
            "booking_reference": extension.booking.booking_reference
        })

    else:
        return jsonify({"success": False, "message": "Unknown payment type"}), 400