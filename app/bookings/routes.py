from flask import render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user, login_user
from app.bookings import bookings_bp
from app import db
from app.models import Booking, Unit, ApartmentType, User
from datetime import datetime
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

@bookings_bp.route('/new', methods=['GET', 'POST'])
def new_booking():
    """Create new booking - for authenticated users or guests"""
    if request.method == 'POST':
        data = request.get_json()
        unit_id = data.get('unit_id')
        check_in = datetime.fromisoformat(data.get('check_in'))
        check_out = datetime.fromisoformat(data.get('check_out'))
        num_guests = data.get('num_guests', 2)
        special_requests = data.get('special_requests', '')
        
        unit = Unit.query.get_or_404(unit_id)
        
        # Calculate price
        days = (check_out - check_in).days
        total_price = days * unit.apartment_type.base_price
        
        # Generate unique booking reference
        booking_ref = f'ENI-{uuid.uuid4().hex[:8].upper()}'
        
        # Generate guest code for unregistered guests
        guest_code = None
        is_guest_booking = False
        guest_email = None
        guest_phone = None
        user_id = None
        
        if current_user.is_authenticated:
            user_id = current_user.id
        else:
            # This is a guest booking
            is_guest_booking = True
            guest_code = generate_guest_code()
            guest_email = data.get('guest_email')
            guest_phone = data.get('guest_phone')
            
            # Try to find or create user for guest
            existing_user = User.query.filter_by(email=guest_email).first()
            if existing_user:
                user_id = existing_user.id
            else:
                # Create temporary guest user
                guest_user = User(
                    email=guest_email,
                    first_name=data.get('guest_first_name', 'Guest'),
                    last_name=data.get('guest_last_name', ''),
                    phone=guest_phone,
                    password_hash=''
                )
                db.session.add(guest_user)
                db.session.flush()
                user_id = guest_user.id
        
        # Create booking
        booking = Booking(
            booking_reference=booking_ref,
            user_id=user_id,
            unit_id=unit_id,
            check_in_date=check_in,
            check_out_date=check_out,
            number_of_guests=num_guests,
            total_price=total_price,
            status='pending',
            special_requests=special_requests,
            guest_code=guest_code,
            is_guest_booking=is_guest_booking,
            guest_email=guest_email,
            guest_phone=guest_phone
        )
        
        db.session.add(booking)
        db.session.commit()
        
        return jsonify({'success': True, 'booking_id': booking.id, 'guest_code': guest_code})
    
    if current_user.is_authenticated:
        return render_template('bookings/new.html')
    else:
        return render_template('bookings/new.html')

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
