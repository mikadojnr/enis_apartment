from flask import render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user, login_user
from app.bookings import bookings_bp
from app import db
from app.models import Booking, Unit, ApartmentType, User
from datetime import datetime, time, timedelta
import uuid
import string
import random

from flask_mail import Message
from app import mail
from flask import current_app


def generate_guest_code():
    """Generate a unique 6-character guest booking code"""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

def send_booking_created_email(booking):
    """Send email when booking is created (awaiting payment)"""
    subject = f"Booking Received - {booking.booking_reference}"
    body = f"""
    Dear {booking.first_name},

    Your booking ({booking.booking_reference}) has been received.

    Unit: {booking.unit.unit_number}
    Check-in: {booking.check_in_date.strftime('%d %b %Y')} at 3:00 PM
    Check-out: {booking.check_out_date.strftime('%d %b %Y')} at 11:00 AM
    Total: ₦{booking.total_price:,.2f}

    Please complete payment within 10 minutes: 
    {url_for('bookings.booking_confirmation', booking_reference=booking.booking_reference, _external=True)}

    After payment you will receive a confirmation email.

    Thank you!
    Eni's Apartments
    """
    msg = Message(subject, recipients=[booking.email], body=body)
    mail.send(msg)

def send_booking_confirmed_email(booking):
    """Send email after successful payment"""
    subject = f"Booking Confirmed - {booking.booking_reference}"
    body = f"""
    Dear {booking.first_name},

    Your payment has been received and your booking is now confirmed!

    Booking Reference: {booking.booking_reference}
    Unit: {booking.unit.unit_number}
    Check-in: {booking.check_in_date.strftime('%d %b %Y')} 3:00 PM
    Check-out: {booking.check_out_date.strftime('%d %b %Y')} 11:00 AM

    View details or manage your booking:
    {url_for('bookings.booking_details', booking_reference=booking.booking_reference, _external=True)}

    Enjoy your stay!
    Eni's Apartments
    """
    msg = Message(subject, recipients=[booking.email], body=body)
    mail.send(msg)


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
def new_booking():

    if request.method == 'GET':
        return render_template('bookings/new.html')
    
    if not request.is_json:
        return jsonify({"success": False, "message": "JSON required"}), 415

    data = request.get_json()

    required = ['unit_id', 'check_in', 'check_out', 'first_name', 'last_name', 'email', 'phone']
    missing = [f for f in required if f not in data or not data[f]]
    if missing:
        return jsonify({"success": False, "message": f"Missing: {', '.join(missing)}"}), 400

    try:
        check_in  = datetime.strptime(data['check_in'],  "%Y-%m-%d")
        check_out = datetime.strptime(data['check_out'], "%Y-%m-%d")
    except ValueError:
        return jsonify({"success": False, "message": "Invalid date format"}), 400

    if check_out <= check_in:
        return jsonify({"success": False, "message": "Invalid dates"}), 400

    unit = Unit.query.get_or_404(data['unit_id'])

    days = (check_out - check_in).days
    if days <= 0:
        return jsonify({"success": False, "message": "Invalid duration"}), 400

    base_total = days * float(unit.apartment_type.base_price)

    user_id = current_user.id if current_user.is_authenticated else None
    guest_code = None
    is_guest = False

    if not user_id:
        is_guest = True
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
        booking_reference = f"ENI-{uuid.uuid4().hex[:8].upper()}",
        user_id           = user_id,
        unit_id           = unit.id,
        first_name        = str(data['first_name']).strip(),
        last_name         = str(data['last_name']).strip(),
        email             = str(data['email']).strip().lower(),
        phone             = str(data['phone']).strip(),
        id_type           = data.get('id_type'),
        check_in_date     = check_in,
        check_out_date    = check_out,
        num_adults        = int(data.get('num_adults', 0)),
        num_children      = int(data.get('num_children', 0)),
        number_of_guests  = int(data.get('num_adults', 0)) + int(data.get('num_children', 0)),
        total_price       = base_total,
        status            = 'pending',
        special_requests  = data.get('special_requests', '').strip(),
        is_guest_booking  = is_guest,
        guest_code        = guest_code,
        guest_email       = data['email'] if is_guest else None,
        guest_phone       = data['phone'] if is_guest else None,
        expires_at        = datetime.utcnow() + timedelta(minutes=10)
    )

    addon_ids = data.get('addons', [])
    if addon_ids:
        booking.addons = Service.query.filter(Service.id.in_(addon_ids)).all()

    db.session.add(booking)
    db.session.commit()

    # Send email
    try:
        send_booking_created_email(booking)
    except Exception as e:
        current_app.logger.error(f"Email send failed: {e}")

    return jsonify({
        "success": True,
        "booking_reference": booking.booking_reference
    })

# ────────────────────────────────────────────────────────────────
# Confirmation page with countdown
# ────────────────────────────────────────────────────────────────
@bookings_bp.route('/<string:booking_reference>')
def booking_confirmation(booking_reference):
    booking = Booking.query.filter_by(booking_reference=booking_reference).first_or_404()

    # Auto-expire logic
    now = datetime.utcnow()
    if booking.expires_at and now > booking.expires_at and booking.status == 'pending':
        booking.status = 'expired'
        db.session.commit()

    # Access control
    if current_user.is_authenticated:
        if booking.user_id != current_user.id and not current_user.is_admin:
            flash("You don't have permission to view this booking", "danger")
            return redirect(url_for('main.index'))
    else:
        # Guest – for now allow anyone with the reference (can be hardened later)
        pass

    return render_template('bookings/confirmation.html', booking=booking)

# ────────────────────────────────────────────────────────────────
# Simulate / handle payment success (in real app this would be webhook or verify endpoint)
# ────────────────────────────────────────────────────────────────
@bookings_bp.route('/<string:booking_reference>/payment-success', methods=['POST'])
def payment_success(booking_reference):
    booking = Booking.query.filter_by(booking_reference=booking_reference).first_or_404()

    if booking.status != 'pending':
        return jsonify({"success": False, "message": "Booking not in payable state"}), 400

    booking.status = 'confirmed'
    booking.paid = True
    booking.expires_at = None
    db.session.commit()

    try:
        send_booking_confirmed_email(booking)
    except Exception as e:
        current_app.logger.error(f"Confirmation email failed: {e}")

    return jsonify({"success": True, "message": "Payment confirmed"})

# ────────────────────────────────────────────────────────────────
# Details page (after payment / for logged-in users)
# ────────────────────────────────────────────────────────────────
@bookings_bp.route('/details/<string:booking_reference>')
def booking_details(booking_reference):
    booking = Booking.query.filter_by(booking_reference=booking_reference).first_or_404()

    if current_user.is_authenticated:
        if booking.user_id != current_user.id and not current_user.is_admin:
            flash("Unauthorized", "danger")
            return redirect(url_for('main.index'))
    else:
        # Guest access – optionally require guest_code or just reference
        pass

    return render_template('bookings/details.html', booking=booking)

@bookings_bp.route('/guest/<guest_code>')
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
    """Guest dashboard"""
    bookings = current_user.bookings.all()
    service_requests = current_user.service_requests.all()
    
    return render_template('guest/dashboard.html',
                         bookings=bookings,
                         service_requests=service_requests)

@bookings_bp.route('/<int:booking_id>/cancel', methods=['POST'])
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
