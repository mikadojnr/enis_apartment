from flask import app, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user, login_user
from app.bookings import bookings_bp
from app import db
from app.models import Booking, Payment, Service, ServiceRequest, Unit, ApartmentType, User, VerifiedID
from datetime import datetime, time, timedelta
import uuid
import string
import random

from flask_mail import Message
from app import mail
from flask import current_app
from flask_wtf.csrf import generate_csrf


def generate_guest_code():
    """Generate a unique 6-character guest booking code"""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

def send_booking_created_email(booking):
    """Send HTML email when a new booking is created (awaiting payment)"""
    try:
        subject = f"Booking Received – {booking.booking_reference}"

        html_body = render_template(
            'emails/booking_created.html',
            first_name=booking.first_name,
            booking_reference=booking.booking_reference,
            unit_number=booking.unit.unit_number,
            check_in_date=booking.check_in_date.strftime('%d %b %Y'),
            check_out_date=booking.check_out_date.strftime('%d %b %Y'),
            total_price=f"₦{booking.total_price:,.2f}",
            payment_url=url_for('bookings.booking_confirmation',
                               booking_reference=booking.booking_reference,
                               _external=True)
        )
        
        # current_app.logger.info(f"Unit: {booking.unit}")

        msg = Message(
            subject=subject,
            recipients=[booking.email],
            body="Your booking has been received.",
            html=html_body,
            sender=current_app.config['MAIL_DEFAULT_SENDER']
        )

        print(html_body)
        # current_app.logger.info(f"Email sent successfully to {booking.email}")
        
        mail.send(msg)
        # current_app.logger.info(f"Booking created email sent successfully to {booking.email}")
    except Exception as e:
        current_app.logger.error(f"Failed to send booking created email to {booking.email}: {str(e)}", exc_info=True)
        raise

def send_booking_confirmed_email(booking):
    """Send HTML email after successful payment confirmation"""
    try:
        subject = f"Booking Confirmed – {booking.booking_reference}"

        html_body = render_template(
            'emails/booking_confirmed.html',
            first_name=booking.first_name,
            booking_reference=booking.booking_reference,
            unit_number=booking.unit.unit_number,
            check_in_date=booking.check_in_date.strftime('%d %b %Y'),
            check_out_date=booking.check_out_date.strftime('%d %b %Y'),
            details_url=url_for('bookings.booking_details',
                               booking_reference=booking.booking_reference,
                               _external=True),
            current_year=datetime.utcnow().year
        )

        msg = Message(
            subject=subject,
            recipients=[booking.email],
            html=html_body,
            sender=current_app.config.get('MAIL_DEFAULT_SENDER')
        )
    
        mail.send(msg)
        # current_app.logger.info(f"Booking confirmed email sent successfully to {booking.email}")
    except Exception as e:
        current_app.logger.error(f"Failed to send booking confirmed email to {booking.email}: {str(e)}", exc_info=True)


@bookings_bp.route('/availability')
def availability():
    """Check availability - for searching across all units"""
    check_in = request.args.get('check_in')
    check_out = request.args.get('check_out')
    apartment_type = request.args.get('type')
    
    units = Unit.query
    if apartment_type:
        units = units.filter_by(apartment_type_id=apartment_type)
    
    units = units.all()
    apartment_types = ApartmentType.query.all()
    
    return render_template('bookings/availability.html',
                         units=units,
                         apartment_types=apartment_types,
                         check_in=check_in,
                         check_out=check_out)

@bookings_bp.route('/new', methods=['GET', 'POST'])
@login_required
def new_booking():
    if request.method == 'GET':
        return render_template('bookings/new.html')

    # POST – create new booking
    if not request.is_json:
        return jsonify({"success": False, "message": "JSON payload required"}), 415

    data = request.get_json()

    # === ID Verification Check ===
    email = str(data.get('email', '')).strip().lower()
    id_type = data.get('id_type')

    # If user is logged in or has previously verified ID with this email
    verified = False
    if current_user.is_authenticated:
        verified = VerifiedID.query.filter_by(user_id=current_user.id, is_verified=True).first()
    else:
        verified = VerifiedID.query.filter_by(email=email, is_verified=True).first()

    if not verified and not data.get('verified_id_id'):
        return jsonify({
            "success": False,
            "message": "ID verification required before booking"
        }), 400

    required = ['unit_id', 'check_in', 'check_out', 'first_name', 'last_name', 'email', 'phone']
    missing = [f for f in required if f not in data or not data[f]]
    if missing:
        return jsonify({"success": False, "message": f"Missing required fields: {', '.join(missing)}"}), 400

    try:
        check_in = datetime.strptime(data['check_in'], "%Y-%m-%d")
        check_out = datetime.strptime(data['check_out'], "%Y-%m-%d")
    except ValueError:
        return jsonify({"success": False, "message": "Invalid date format (expected YYYY-MM-DD)"}), 400

    if check_out <= check_in:
        return jsonify({"success": False, "message": "Check-out date must be after check-in"}), 400

    unit = Unit.query.get_or_404(data['unit_id'])

    days = (check_out - check_in).days
    if days <= 0:
        return jsonify({"success": False, "message": "Invalid stay duration"}), 400

    base_total = days * float(unit.apartment_type.base_price)

    user_id = current_user.id if current_user.is_authenticated else None
    guest_code = None
    is_guest_booking = False

    if not user_id:
        is_guest_booking = True
        guest_code = generate_guest_code()
        email = str(data['email']).strip().lower()
        existing = User.query.filter_by(email=email).first()
        if existing:
            user_id = existing.id
        else:
            new_user = User(
                email=email,
                first_name=str(data['first_name']).strip(),
                last_name=str(data['last_name']).strip(),
                phone=str(data['phone']).strip(),
                password_hash='',
                is_admin=False
            )
            db.session.add(new_user)
            db.session.flush()
            user_id = new_user.id

    booking = Booking(
        booking_reference=f"ENI-{uuid.uuid4().hex[:8].upper()}",
        user_id=user_id,
        unit_id=unit.id,
        first_name=str(data['first_name']).strip(),
        last_name=str(data['last_name']).strip(),
        email=str(data['email']).strip().lower(),
        phone=str(data['phone']).strip(),
        id_type=data.get('id_type'),
        check_in_date=check_in,
        check_out_date=check_out,
        num_adults=int(data.get('num_adults', 0)),
        num_children=int(data.get('num_children', 0)),
        number_of_guests=int(data.get('num_adults', 0)) + int(data.get('num_children', 0)),
        total_price=base_total,
        status='pending',
        special_requests=data.get('special_requests', '').strip(),
        is_guest_booking=is_guest_booking,
        guest_code=guest_code,
        guest_email=data['email'] if is_guest_booking else None,
        guest_phone=data['phone'] if is_guest_booking else None,
        expires_at=datetime.utcnow() + timedelta(minutes=10)
    )

    addon_ids = data.get('addons', [])
    if addon_ids:
        booking.addons = Service.query.filter(Service.id.in_(addon_ids)).all()

    db.session.add(booking)
    db.session.commit()

    # Send notification email (awaiting payment)
    send_booking_created_email(booking)

    return jsonify({
        "success": True,
        "booking_reference": booking.booking_reference,
        "message": "Booking created successfully. Please complete payment within 10 minutes."
    }), 201


@bookings_bp.route('/<string:booking_reference>/payment-success', methods=['POST'])
@login_required
def payment_success(booking_reference):
    """
    Endpoint called after successful payment (via Paystack callback or webhook)
    - Creates Payment record
    - Updates Booking to confirmed/paid
    - Sends confirmation email
    """
    booking = Booking.query.filter_by(booking_reference=booking_reference).first_or_404()

    if booking.status != 'pending':
        return jsonify({"success": False, "message": "Booking is no longer in payable state"}), 400

    # In production: verify Paystack webhook signature / payload here
    # For now we accept the payload from frontend or simulate
    payload = request.get_json() or {}

    paystack_ref = payload.get('reference') or f"PAY-{uuid.uuid4().hex[:8].upper()}"
    amount_paid = float(payload.get('amount', booking.total_price * 1.05))  # fallback to full amount

    # Record the payment
    payment = Payment(
        booking_id=booking.id,
        payment_reference=paystack_ref,
        amount=amount_paid,
        status='success',
        payment_method='paystack',
        gateway_response=str(payload),  # store raw response for audit
    )

    # Update booking status
    booking.status = 'confirmed'
    booking.paid = True
    booking.expires_at = None

    db.session.add(payment)
    db.session.commit()

    # Send confirmation email to guest
    send_booking_confirmed_email(booking)

    return jsonify({
        "success": True,
        "message": "Payment confirmed. Booking is now active.",
        "payment_reference": paystack_ref,
        "booking_reference": booking.booking_reference
    }), 200

# ────────────────────────────────────────────────────────────────
# Confirmation page with countdown
# ────────────────────────────────────────────────────────────────
@bookings_bp.route('/<string:booking_reference>')
@login_required
def booking_confirmation(booking_reference):
    booking = Booking.query.filter_by(booking_reference=booking_reference).first_or_404()

    # Auto-expire logic
    now = datetime.utcnow()
    if booking.expires_at and now > booking.expires_at and booking.status == 'pending':
        booking.status = 'expired'
        db.session.commit()

    # Access control (your existing logic)
    if current_user.is_authenticated:
        if booking.user_id != current_user.id and not current_user.is_admin:
            flash("You don't have permission to view this booking", "danger")
            return redirect(url_for('main.index'))

    return render_template(
        'bookings/confirmation.html',
        booking=booking,
        paystack_public_key=current_app.config.get('PAYSTACK_PUBLIC_KEY'),
        csrf_token=generate_csrf()
    )

# ────────────────────────────────────────────────────────────────
# Details page (after payment / for logged-in users)
# ────────────────────────────────────────────────────────────────
@bookings_bp.route('/details/<string:booking_reference>')
@login_required
def booking_details(booking_reference):
    booking = Booking.query.filter_by(booking_reference=booking_reference).first_or_404()

    # Authorization check
    if booking.user_id != current_user.id and not current_user.is_admin:
        flash("Unauthorized access", "danger")
        return redirect(url_for('main.index'))

    # Decide which base template to use
    if current_user.is_admin:
        base_template = 'base.html'           # Full site base with navigation + footer
    else:
        base_template = 'bookings/base.html'  # Minimal base (no nav/footer for booking pages)

    return render_template(
        'bookings/details.html',
        booking=booking,
        base_template=base_template          # Pass this to the template
    )
@bookings_bp.route('/guest/<guest_code>')
@login_required
def guest_booking_access(guest_code):
    """Allow guests to access booking via code"""
    booking = Booking.query.filter_by(guest_code=guest_code).first_or_404()
    
    # Check if code is still valid (within booking dates)
    now = datetime.utcnow()
    if now > booking.check_out_date:
        flash('This booking code has expired', 'warning')
        return redirect(url_for('main.index'))
    
    return render_template('bookings/details.html', booking=booking, guest_code=guest_code)

@bookings_bp.route('/dashboard')
@login_required
def dashboard():
    bookings = current_user.bookings.all()
    service_requests = current_user.service_requests.all()

    # Calculate total spent (only confirmed/paid bookings)
    total_spent = sum(b.total_price for b in bookings if b.paid and b.status == 'confirmed')

    return render_template(
        'bookings/dashboard.html',
        bookings=bookings,
        service_requests=service_requests,
        active_bookings_count=len([b for b in bookings if b.status == 'confirmed']),
        pending_services_count=len([r for r in service_requests if r.status == 'pending']),
        total_spent=total_spent,
        upcoming_booking=next((b for b in bookings if b.status == 'confirmed' and b.check_in_date > datetime.utcnow()), None)
    )

@bookings_bp.route('/<int:booking_id>/cancel', methods=['POST'])
@login_required
def cancel_booking(booking_id):
    """Cancel booking"""
    booking = Booking.query.get_or_404(booking_id)
    guest_code = request.args.get('code')
    
    # Check permissions
    if current_user.is_authenticated:
        if booking.user_id != current_user.id and not current_user.is_admin:
            return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    else:
        if not booking.guest_code or booking.guest_code != guest_code:
            return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    booking.status = 'cancelled'
    db.session.commit()
    
    flash('Booking cancelled', 'info')
    if current_user.is_authenticated:
        return redirect(url_for('bookings.dashboard'))
    else:
        return jsonify({'success': True})

@bookings_bp.route('/<string:booking_reference>/status')
@login_required
def booking_status(booking_reference):
    booking = Booking.query.filter_by(booking_reference=booking_reference).first_or_404()
    return jsonify({
        "status": booking.status,
        "paid": booking.paid,
        "expires_at": booking.expires_at.isoformat() if booking.expires_at else None,
        "message": "Booking status retrieved"
    })


# ====================== SERVICE REQUESTS ======================
@bookings_bp.route('/service-request', methods=['POST'])
@login_required
def create_service_request():
    """Create a new service request - Only for active confirmed bookings"""
    data = request.get_json()

    booking_id = data.get('booking_id')
    service_id = data.get('service_id')
    notes = data.get('notes', '').strip()

    if not booking_id or not service_id:
        return jsonify({"success": False, "message": "Booking and Service are required"}), 400

    booking = Booking.query.get_or_404(booking_id)

    # === STRICT VALIDATION FOR ACTIVE BOOKINGS ===
    now = datetime.utcnow().date()

    if booking.user_id != current_user.id:
        return jsonify({"success": False, "message": "Unauthorized"}), 403

    if booking.status != 'confirmed':
        return jsonify({"success": False, "message": "Service requests are only allowed for confirmed bookings"}), 400

    if not booking.paid:
        return jsonify({"success": False, "message": "Booking must be fully paid"}), 400

    if booking.check_out_date.date() < now:
        return jsonify({"success": False, "message": "This booking has already ended"}), 400

    # Optional: Allow requests up to 1 day before check-in
    if booking.check_in_date.date() > now + timedelta(days=1):
        return jsonify({"success": False, "message": "Service requests are only available for current or imminent stays"}), 400

    service = Service.query.get_or_404(service_id)

    service_request = ServiceRequest(
        service_id=service.id,
        booking_id=booking.id,
        user_id=current_user.id,
        unit_id=booking.unit_id,
        status='pending',
        notes=notes
    )

    db.session.add(service_request)
    db.session.commit()

    # Send emails
    send_new_service_request_email(service_request)
    send_service_request_confirmation_email(service_request)

    return jsonify({
        "success": True,
        "message": f"Request for '{service.name}' has been submitted successfully.",
        "request_id": service_request.id
    }), 201

def send_new_service_request_email(service_request):
    """Notify Admin when a new service request is made"""
    try:
        subject = f"New Service Request - {service_request.service.name}"
        html_body = render_template(
            'emails/admin_new_service_request.html',
            request=service_request,
            guest=service_request.requester,
            booking=service_request.booking,
            unit=service_request.booking.unit
        )
        msg = Message(
            subject=subject,
            recipients=[current_app.config['MAIL_DEFAULT_SENDER']],  # Admin email
            html=html_body,
            sender=current_app.config['MAIL_DEFAULT_SENDER']
        )
        mail.send(msg)
    except Exception as e:
        current_app.logger.error(f"Failed to send admin service request notification: {str(e)}")


def send_service_request_confirmation_email(service_request):
    """Send confirmation to guest"""
    try:
        subject = f"Service Request Received - {service_request.service.name}"
        html_body = render_template(
            'emails/guest_service_request_confirmation.html',
            request=service_request,
            guest=service_request.requester,
            booking=service_request.booking
        )
        msg = Message(
            subject=subject,
            recipients=[service_request.requester.email],
            html=html_body,
            sender=current_app.config['MAIL_DEFAULT_SENDER']
        )
        mail.send(msg)
    except Exception as e:
        current_app.logger.error(f"Failed to send guest service request confirmation: {str(e)}")

@bookings_bp.route('/service-requests')
@login_required
def get_service_requests():
    """Get all service requests for current user"""
    requests = ServiceRequest.query.filter_by(user_id=current_user.id)\
        .order_by(ServiceRequest.created_at.desc()).all()

    return jsonify([{
        'id': r.id,
        'service_name': r.service.name,
        'status': r.status,
        'notes': r.notes,
        'unit_number': r.unit.unit_number,
        'created_at': r.created_at.strftime('%d %b %Y, %I:%M %p'),
        'booking_reference': r.booking.booking_reference
    } for r in requests])