from flask import render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user, login_user
from app.bookings import bookings_bp
from app import db
from app.models import Booking, Unit, ApartmentType, User
from datetime import datetime, time
import uuid
import string
import random

def generate_guest_code():
    """Generate a unique 6-character guest booking code"""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

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

@bookings_bp.route('/new', methods=['POST'])
def new_booking():
    data = request.get_json() or {}
    
    required = ['unit_id', 'check_in', 'check_out', 'first_name', 'last_name', 'email', 'phone']
    missing = [f for f in required if not data.get(f)]
    if missing:
        return jsonify({"success": False, "message": f"Missing fields: {', '.join(missing)}"}), 400

    try:
        # ───── Dates ─────
        check_in  = datetime.strptime(data['check_in'],  "%Y-%m-%d")
        check_out = datetime.strptime(data['check_out'], "%Y-%m-%d")
    except ValueError:
        return jsonify({"success": False, "message": "Invalid date format (use YYYY-MM-DD)"}), 400

    if check_out <= check_in:
        return jsonify({"success": False, "message": "Check-out must be after check-in"}), 400

    unit = Unit.query.get_or_404(data['unit_id'])

    days = (check_out - check_in).days
    if days <= 0:
        return jsonify({"success": False, "message": "Invalid stay duration"}), 400

    # Base price
    base_total = days * unit.apartment_type.base_price

    # ───── Guest / User handling ─────
    user_id = None
    guest_code = None
    is_guest_booking = False

    if current_user.is_authenticated:
        user_id = current_user.id
    else:
        # Guest flow
        is_guest_booking = True
        guest_code = generate_guest_code()   # your function

        email = data['email'].strip().lower()
        existing = User.query.filter_by(email=email).first()

        if existing:
            user_id = existing.id
        else:
            # Create minimal user record
            new_user = User(
                email=email,
                first_name=data['first_name'].strip(),
                last_name=data['last_name'].strip(),
                phone=data['phone'].strip(),
                password_hash='',           # no password → guest
                is_admin=False
            )
            db.session.add(new_user)
            db.session.flush()
            user_id = new_user.id

    # ───── Create Booking ─────
    booking = Booking(
        booking_reference = f"ENI-{uuid.uuid4().hex[:8].upper()}",
        user_id           = user_id,
        unit_id           = unit.id,
        
        first_name        = data['first_name'].strip(),
        last_name         = data['last_name'].strip(),
        email             = data['email'].strip().lower(),
        phone             = data['phone'].strip(),
        id_type           = data.get('id_type'),
        
        check_in_date     = check_in,
        check_out_date    = check_out,
        
        num_adults        = int(data.get('num_adults', 0)),
        num_children      = int(data.get('num_children', 0)),
        number_of_guests  = int(data.get('num_adults', 0)) + int(data.get('num_children', 0)),
        
        total_price       = base_total,           # → you can improve later with addons
        status            = 'pending',
        special_requests  = data.get('special_requests', '').strip(),
        
        is_guest_booking  = is_guest_booking,
        guest_code        = guest_code,
        guest_email       = data['email'] if is_guest_booking else None,
        guest_phone       = data['phone'] if is_guest_booking else None,
        
        # 24 hours expiry
        expires_at        = datetime.utcnow() + timedelta(hours=24)
    )

    # ───── Add-ons ─────
    addon_ids = data.get('addons', [])   # list of service IDs
    if addon_ids:
        selected_services = Service.query.filter(Service.id.in_(addon_ids)).all()
        booking.addons = selected_services

    db.session.add(booking)
    db.session.commit()

    return jsonify({
        "success": True,
        "booking_reference": booking.booking_reference,
        "booking_id": booking.id,           # keep for compatibility
        "expires_at": booking.expires_at.isoformat() if booking.expires_at else None,
        "total_price": booking.total_price
    })

@bookings_bp.route('/<int:booking_id>/confirmation')
def booking_confirmation(booking_id):
    """View booking confirmation"""
    booking = Booking.query.get_or_404(booking_id)
    
    # Allow access if authenticated user owns it, or guest with correct code in session
    if current_user.is_authenticated:
        if booking.user_id != current_user.id and not current_user.is_admin:
            flash('Unauthorized', 'danger')
            return redirect(url_for('main.index'))
    else:
        # Guest access via code
        guest_code = request.args.get('code', request.session.get('guest_code'))
        if booking.guest_code != guest_code:
            flash('Invalid access code', 'danger')
            return redirect(url_for('main.index'))
    
    return render_template('bookings/confirmation.html', booking=booking)

@bookings_bp.route('/<int:booking_id>')
def booking_details(booking_id):
    """View booking details"""
    booking = Booking.query.get_or_404(booking_id)
    guest_code = request.args.get('code')
    
    # Check access permissions
    if current_user.is_authenticated:
        if booking.user_id != current_user.id and not current_user.is_admin:
            flash('Unauthorized', 'danger')
            return redirect(url_for('main.index'))
    else:
        # Guest access via code
        if not booking.guest_code or booking.guest_code != guest_code:
            flash('Invalid access code', 'danger')
            return redirect(url_for('main.index'))
    
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
