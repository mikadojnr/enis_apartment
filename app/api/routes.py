from flask import jsonify, request
from app.api import api_bp
from app.models import Unit, Service, Booking
from datetime import datetime

@api_bp.route('/units')
def get_units():
    """Get all units"""
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

# @api_bp.route('/units/<int:unit_id>')
# def get_unit(unit_id):
#     """Get unit details"""
#     unit = Unit.query.get_or_404(unit_id)
#     return jsonify({
#         'id': unit.id,
#         'unit_number': unit.unit_number,
#         'floor': unit.floor,
#         'view': unit.view,
#         'is_available': unit.is_available,
#         'apartment_type': {
#             'name': unit.apartment_type.name,
#             'bedrooms': unit.apartment_type.bedrooms,
#             'bathrooms': unit.apartment_type.bathrooms,
#             'area_sqm': unit.apartment_type.area_sqm,
#             'base_price': unit.apartment_type.base_price,
#             'description': unit.apartment_type.description
#         }
#     })


@api_bp.route('/units/<int:unit_id>')
def get_unit(unit_id):
    """Get unit details, including all related data"""
    unit = Unit.query.get_or_404(unit_id)
    
    # Fetch related data for unit
    apartment_type = unit.apartment_type
    unit_images = unit.gallery_images if unit.gallery_images else []
    bookings = unit.bookings.all() if unit.bookings else []
    service_requests = unit.service_requests.all() if unit.service_requests else []
    
    # Create a response dictionary
    unit_data = {
        'id': unit.id,
        'unit_number': unit.unit_number,
        'floor': unit.floor,
        'view': unit.view,
        'is_available': unit.is_available,
        'created_at': unit.created_at,
        'updated_at': unit.updated_at,
        'apartment_type': {
            'name': apartment_type.name,
            'bedrooms': apartment_type.bedrooms,
            'bathrooms': apartment_type.bathrooms,
            'area_sqm': apartment_type.area_sqm,
            'base_price': apartment_type.base_price,
            'description': apartment_type.description,
        },
        'images': [
            {
                'id': image.id,
                'image_url': image.image_url,
                'label': image.label,
                'description': image.description,
                'is_featured': image.is_featured,
                'created_at': image.created_at
            }
            for image in unit_images
        ],
        'bookings': [
            {
                'booking_reference': booking.booking_reference,
                'check_in_date': booking.check_in_date,
                'check_out_date': booking.check_out_date,
                'number_of_guests': booking.number_of_guests,
                'status': booking.status,
                'total_price': booking.total_price,
                'paid': booking.paid,
                'special_requests': booking.special_requests,
                'guest_email': booking.guest_email,
                'guest_phone': booking.guest_phone,
                'created_at': booking.created_at
            }
            for booking in bookings
        ],
        'service_requests': [
            {
                'service_id': service_request.service_id,
                'status': service_request.status,
                'notes': service_request.notes,
                'created_at': service_request.created_at,
                'updated_at': service_request.updated_at
            }
            for service_request in service_requests
        ]
    }

    return jsonify(unit_data)

@api_bp.route('/services')
def get_services():
    """Get all services"""
    services = Service.query.filter_by(is_active=True).all()
    return jsonify([{
        'id': s.id,
        'name': s.name,
        'category': s.category,
        'description': s.description,
        'price': s.price
    } for s in services])

@api_bp.route('/availability', methods=['GET'])
def check_availability():
    """Check unit availability for date range"""
    unit_id = request.args.get('unit_id', type=int)
    check_in = request.args.get('check_in')
    check_out = request.args.get('check_out')
    
    if not all([unit_id, check_in, check_out]):
        return jsonify({'error': 'Missing parameters'}), 400
    
    try:
        check_in_date = datetime.fromisoformat(check_in)
        check_out_date = datetime.fromisoformat(check_out)
    except ValueError:
        return jsonify({'error': 'Invalid date format'}), 400
    
    # Check for overlapping bookings
    overlapping = Booking.query.filter(
        Booking.unit_id == unit_id,
        Booking.status.in_(['pending', 'confirmed']),
        Booking.check_in_date < check_out_date,
        Booking.check_out_date > check_in_date
    ).count()
    
    is_available = overlapping == 0
    
    return jsonify({
        'unit_id': unit_id,
        'check_in': check_in,
        'check_out': check_out,
        'is_available': is_available
    })

@api_bp.route('/price', methods=['GET'])
def calculate_price():
    """Calculate booking price"""
    unit_id = request.args.get('unit_id', type=int)
    check_in = request.args.get('check_in')
    check_out = request.args.get('check_out')
    
    if not all([unit_id, check_in, check_out]):
        return jsonify({'error': 'Missing parameters'}), 400
    
    unit = Unit.query.get_or_404(unit_id)
    
    try:
        check_in_date = datetime.fromisoformat(check_in)
        check_out_date = datetime.fromisoformat(check_out)
    except ValueError:
        return jsonify({'error': 'Invalid date format'}), 400
    
    days = (check_out_date - check_in_date).days
    if days <= 0:
        return jsonify({'error': 'Invalid date range'}), 400
    
    total_price = days * unit.apartment_type.base_price
    
    return jsonify({
        'unit_id': unit_id,
        'days': days,
        'price_per_day': unit.apartment_type.base_price,
        'total_price': total_price
    })
