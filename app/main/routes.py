from flask import current_app, render_template, request, jsonify, send_from_directory
from flask_login import current_user
from app.main import main_bp
from app import db, mail
from app.models import Unit, Service, Booking, ApartmentType
from flask_mail import Message
from flask_limiter import Limiter
from app import limiter
from datetime import datetime

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
@limiter.limit("5 per minute")
def contact():
    if request.method == 'POST':
        try:
            data = request.get_json()

            name = data.get('name', '').strip()
            email = data.get('email', '').strip()
            phone = data.get('phone', '').strip()
            subject = data.get('subject', 'General Inquiry')
            message_body = data.get('message', '').strip()

            if not all([name, email, message_body]):
                return jsonify({'success': False, 'message': 'Name, email and message are required'}), 400

            # === Email to Admin ===
            admin_msg = Message(
                subject=f"New Contact: {subject} - {name}",
                sender=current_app.config['MAIL_DEFAULT_SENDER'],
                recipients=["stay@enisapartment.com"],
                reply_to=email
            )

            admin_msg.html = render_template(
                'emails/contact_admin.html',
                name=name,
                email=email,
                phone=phone or 'Not provided',
                subject=subject,
                message=message_body
            )

            mail.send(admin_msg)

            # === Auto-reply to User ===
            user_msg = Message(
                subject="Thank you for contacting Eni's Apartments",
                sender=current_app.config['MAIL_DEFAULT_SENDER'],
                recipients=[email]
            )

            user_msg.html = render_template(
                'emails/contact_user_reply.html',
                name=name
            )

            mail.send(user_msg)

            return jsonify({
                'success': True,
                'message': 'Thank you! Your message has been sent successfully.'
            })

        except Exception as e:
            # ← This is the most important part for debugging
            import traceback
            error_detail = traceback.format_exc()
            current_app.logger.error(f"Contact form failed:\n{error_detail}")
            print("=== CONTACT FORM ERROR ===")
            print(error_detail)
            print("=========================")

            return jsonify({
                'success': False,
                'message': 'Sorry, we could not send your message right now. Please try again later.'
            }), 500

    return render_template('contact.html')