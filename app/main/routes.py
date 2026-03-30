from flask import current_app, render_template, request, jsonify, send_from_directory
from flask_login import current_user
from app.main import main_bp
from app import db
from app.models import Unit, Service, Booking, ApartmentType

@main_bp.route('/')
def index():
    """Landing page"""
    units = Unit.query.limit(4).all()
    essential_services = Service.query.filter_by(category='essential', is_active=True).all()
    optional_services = Service.query.filter_by(category='optional', is_active=True).all()
    
    return render_template('index.html', 
                         units=units,
                         essential_services=essential_services,
                         optional_services=optional_services)

@main_bp.route('/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename)
    
@main_bp.route('/units')
def units():
    """All units page"""
    apartment_type = request.args.get('type', None)
    
    query = Unit.query
    if apartment_type:
        query = query.filter_by(apartment_type_id=apartment_type)
    
    units = query.all()
    apartment_types = ApartmentType.query.all()
    
    return render_template('units.html', units=units, apartment_types=apartment_types)

@main_bp.route('/unit/<unit_number>')
def unit_details(unit_number):
    """Individual unit details"""
    unit = Unit.query.filter_by(unit_number=unit_number).first_or_404()
    gallery_images = unit.gallery_images.all()
    return render_template('unit-details.html', unit=unit, gallery_images=gallery_images)

@main_bp.route('/services')
def services():
    """Services page"""
    essential = Service.query.filter_by(category='essential', is_active=True).all()
    optional = Service.query.filter_by(category='optional', is_active=True).all()
    
    return render_template('services.html', essential=essential, optional=optional)

@main_bp.route('/about')
def about():
    """About page"""
    return render_template('about.html')

@main_bp.route('/contact', methods=['GET', 'POST'])
def contact():
    """Contact page"""
    if request.method == 'POST':
        data = request.get_json()
        # TODO: Handle contact form submission
        return jsonify({'success': True, 'message': 'Message sent successfully'})
    
    return render_template('contact.html')
