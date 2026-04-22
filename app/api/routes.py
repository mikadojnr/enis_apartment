from flask import jsonify, request
from flask_login import current_user, login_required
from app.api import api_bp
from app.models import Unit, Service, Booking, User, VerifiedID
from datetime import datetime
from app import db

@api_bp.route('/users')
def get_users():
    users = User.query.filter_by(is_admin=False).all()
    return jsonify([{
        'id': u.id,
        'first_name': u.first_name,
        'last_name': u.last_name,
        'email': u.email,
        'is_admin': u.is_admin
    } for u in users])

@api_bp.route('/me')
@login_required
def api_me():
    if current_user.is_authenticated:
        verified = VerifiedID.query.filter_by(user_id=current_user.id, is_verified=True).first()
        return jsonify({
            "is_authenticated": True,
            "first_name": current_user.first_name,
            "last_name": current_user.last_name,
            "email": current_user.email,
            "phone": current_user.phone,
            "has_verified_id": bool(verified),
            "verified_id_id": verified.id if verified else None,
            "full_name": f"{current_user.first_name} {current_user.last_name}"
        })
    return jsonify({"is_authenticated": False})


@api_bp.route('/my-bookings')
@login_required
def api_my_bookings():
    """Return current user's bookings for dashboard"""
    bookings = Booking.query.filter_by(user_id=current_user.id).order_by(Booking.check_in_date.desc()).all()

    print(f"API: Returning {len(bookings)} bookings for user {current_user.email}")
    
    return jsonify([{
        'id': b.id,
        'booking_reference': b.booking_reference,
        'unit_number': b.unit.unit_number,
        'check_in_date': b.check_in_date.strftime('%Y-%m-%d'),
        'check_out_date': b.check_out_date.strftime('%Y-%m-%d'),
        'status': b.status,
        'paid': b.paid,
        'total_price': float(b.total_price)
    } for b in bookings])


@api_bp.route('/units')
def get_units():
    """Get all units (basic list)"""
    units = Unit.query.all()
    return jsonify([{
        'id': u.id,
        'unit_number': u.unit_number,
        'floor': u.floor,
        'view': u.view,
        'is_available': u.is_available,
        'apartment_type': {
            'name': u.apartment_type.name,
            'bedrooms': u.apartment_type.bedrooms,
            'bathrooms': u.apartment_type.bathrooms,
            'area_sqm': u.apartment_type.area_sqm,
            'price': u.apartment_type.base_price
        }
    } for u in units])

@api_bp.route('/units/<int:unit_id>')
def get_unit(unit_id):
    """Get detailed unit info including addons, images, etc."""
    unit = Unit.query.get_or_404(unit_id)
    
    apartment_type = unit.apartment_type
    unit_images = unit.gallery_images.all() if unit.gallery_images else []
    
    unit_data = {
        'id': unit.id,
        'unit_number': unit.unit_number,
        'floor': unit.floor,
        'view': unit.view,
        'is_available': unit.is_available,
        'created_at': unit.created_at.isoformat() if unit.created_at else None,
        'updated_at': unit.updated_at.isoformat() if unit.updated_at else None,
        'apartment_type': {
            'name': apartment_type.name,
            'bedrooms': apartment_type.bedrooms,
            'bathrooms': apartment_type.bathrooms,
            'area_sqm': apartment_type.area_sqm,
            'base_price': apartment_type.base_price,
            'description': apartment_type.description,
            'amenities': apartment_type.amenities or [],
            'rating': apartment_type.rating,
            'addons': [{
                'id': s.id,
                'name': s.name,
                'description': s.description,
                'price': s.price,
                'pricing_type': s.pricing_type,
                'icon': s.icon,
                'category': s.category,
                'is_active': s.is_active
            } for s in apartment_type.services if s.is_active]
        },
        'images': [{
            'id': img.id,
            'image_url': img.image_url,
            'label': img.label,
            'description': img.description,
            'is_featured': img.is_featured,
            'created_at': img.created_at.isoformat() if img.created_at else None
        } for img in unit_images]
    }

    return jsonify(unit_data)

@api_bp.route('/services')
def get_services():
    """Get all active services"""
    services = Service.query.filter_by(is_active=True).all()
    return jsonify([{
        'id': s.id,
        'name': s.name,
        'category': s.category,
        'description': s.description,
        'price': s.price,
        'pricing_type': s.pricing_type,
        'icon': s.icon
    } for s in services])

@api_bp.route('/availability', methods=['GET'])
def check_availability():
    check_in = request.args.get('check_in')
    check_out = request.args.get('check_out')
    unit_id = request.args.get('unit_id', type=int)

    if not check_in or not check_out:
        return jsonify({'error': 'Missing check_in and check_out parameters'}), 400

    try:
        check_in_date = datetime.fromisoformat(check_in)
        check_out_date = datetime.fromisoformat(check_out)
    except ValueError:
        return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400

    if check_out_date <= check_in_date:
        return jsonify({'error': 'Check-out must be after check-in'}), 400

    now = datetime.utcnow()

    # Query for overlapping bookings (confirmed or active pending)
    overlapping_query = Booking.query.filter(
        db.or_(
            Booking.status == 'confirmed',
            db.and_(
                Booking.status == 'pending',
                db.or_(
                    Booking.expires_at.is_(None),
                    Booking.expires_at > now
                )
            )
        ),
        Booking.check_in_date < check_out_date,
        Booking.check_out_date > check_in_date
    )

    if unit_id:
        # Single unit check (used in unit details page - unchanged behavior)
        overlapping = overlapping_query.filter(Booking.unit_id == unit_id).count()
        return jsonify({
            'unit_id': unit_id,
            'check_in': check_in,
            'check_out': check_out,
            'is_available': overlapping == 0,
            'overlapping_count': overlapping
        })

    # Admin mode: return availability for ALL units
    units = Unit.query.all()
    result = []

    for unit in units:
        count = overlapping_query.filter(Booking.unit_id == unit.id).count()
        result.append({
            'unit_id': unit.id,
            'is_available': count == 0,
            'base_price': float(unit.apartment_type.base_price) if unit.apartment_type else None,
            'unit_number': unit.unit_number,
            'apartment_type': unit.apartment_type.name if unit.apartment_type else ''
        })

    return jsonify(result)

@api_bp.route('/price', methods=['GET'])
def calculate_price():
    """Calculate base price (without addons)"""
    unit_id   = request.args.get('unit_id', type=int)
    check_in  = request.args.get('check_in')
    check_out = request.args.get('check_out')

    if not all([unit_id, check_in, check_out]):
        return jsonify({'error': 'Missing parameters'}), 400

    unit = Unit.query.get_or_404(unit_id)

    try:
        check_in_date  = datetime.fromisoformat(check_in)
        check_out_date = datetime.fromisoformat(check_out)
    except ValueError:
        return jsonify({'error': 'Invalid date format'}), 400

    days = (check_out_date - check_in_date).days
    if days <= 0:
        return jsonify({'error': 'Invalid date range'}), 400

    total_price = days * float(unit.apartment_type.base_price)

    return jsonify({
        'unit_id': unit_id,
        'days': days,
        'price_per_day': float(unit.apartment_type.base_price),
        'total_price': total_price
    })
