import json
import os

from flask import current_app, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from functools import wraps
from flask_wtf.csrf import validate_csrf
from werkzeug.utils import secure_filename
from app.admin import admin_bp
from app import db
from app.bookings.routes import send_booking_confirmed_email, send_booking_created_email
from app.models import Booking, Payment, Unit, Service, ServiceRequest, User, ApartmentType, UnitImage
from datetime import date, datetime, timedelta
import uuid
import string
import random

def admin_required(f):
    """Decorator to require admin access"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('Admin access required', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

def generate_guest_code():
    """Generate a unique 6-character guest booking code"""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    """Admin dashboard"""
    total_bookings = Booking.query.count()
    total_units = Unit.query.count()
    total_users = User.query.count()
    pending_requests = ServiceRequest.query.filter_by(status='pending').count()
    
    recent_bookings = Booking.query.order_by(Booking.created_at.desc()).limit(5).all()
    
    return render_template('admin/dashboard.html',
                         total_bookings=total_bookings,
                         total_units=total_units,
                         total_users=total_users,
                         pending_requests=pending_requests,
                         recent_bookings=recent_bookings)

@admin_bp.route('/create-booking', methods=['GET', 'POST'])
@login_required
@admin_required
def create_booking():
    if request.method == 'POST':
        data = request.form.to_dict()

        try:
            unit = Unit.query.get_or_404(int(data['unit_id']))
            check_in = datetime.fromisoformat(data['check_in'])
            check_out = datetime.fromisoformat(data['check_out'])
        except (KeyError, ValueError, TypeError):
            return jsonify({'success': False, 'message': 'Invalid date or unit data'}), 400

        days = (check_out - check_in).days
        if days <= 0:
            return jsonify({'success': False, 'message': 'Check-out must be after check-in'}), 400

        base_total = days * float(unit.apartment_type.base_price)

        # Add-ons
        addons_ids = json.loads(data.get('addons', '[]'))
        selected_addons = Service.query.filter(Service.id.in_(addons_ids)).all() if addons_ids else []
        addons_total = sum(svc.price for svc in selected_addons)
        total_price = base_total + addons_total

        guest_code = generate_guest_code()

        # ====================== Guest Handling ======================
        user_id = None
        is_guest_booking = False
        guest_email = None
        guest_phone = None

        if data['guest_type'] == 'registered':
            user_id = int(data['user_id'])
        else:
            is_guest_booking = True
            guest_email = data.get('email')
            guest_phone = data.get('phone')

            existing = User.query.filter_by(email=guest_email).first()
            if existing:
                user_id = existing.id
            else:
                new_user = User(
                    email=guest_email,
                    first_name=data.get('first_name', ''),
                    last_name=data.get('last_name', ''),
                    phone=guest_phone,
                    password_hash=''
                )
                db.session.add(new_user)
                db.session.flush()
                user_id = new_user.id

        # ====================== ID Upload ======================
        id_upload_url = None
        if 'id_upload' in request.files:
            file = request.files['id_upload']
            if file and file.filename:
                filename = secure_filename(file.filename)
                upload_path = os.path.join('uploads/ids', filename)
                os.makedirs(os.path.dirname(upload_path), exist_ok=True)
                file.save(upload_path)
                id_upload_url = f"/{upload_path}"

        # ====================== Create Booking ======================
        mark_paid = data.get('mark_paid') == 'on'

        booking = Booking(
            booking_reference=f"ENI-{uuid.uuid4().hex[:8].upper()}",
            user_id=user_id,
            unit_id=unit.id,
            first_name=data.get('first_name', ''),
            last_name=data.get('last_name', ''),
            email=data.get('email', guest_email),
            phone=data.get('phone', guest_phone),
            check_in_date=check_in,
            check_out_date=check_out,
            number_of_guests=int(data['number_of_guests']),
            total_price=total_price,
            status='confirmed' if mark_paid else 'pending',
            paid=mark_paid,
            special_requests=data.get('special_requests', ''),
            guest_code=guest_code,
            is_guest_booking=is_guest_booking,
            guest_email=guest_email,
            guest_phone=guest_phone,
            id_upload_url=id_upload_url,
            # === NEW: Expiry logic ===
            expires_at=None if mark_paid else datetime.utcnow() + timedelta(minutes=10)
        )

        # Add addons
        if selected_addons:
            booking.addons = selected_addons

        db.session.add(booking)
        db.session.flush()   # So we can use booking.id for Payment

        # ====================== Create Payment Record if Marked Paid ======================
        if mark_paid:
            payment = Payment(
                booking_id=booking.id,
                payment_reference=f"PAY-{uuid.uuid4().hex[:12].upper()}",
                amount=total_price,
                currency='NGN',
                status='success',
                payment_method='admin_marked_paid',
                transaction_date=datetime.utcnow(),
                gateway_response='Marked as paid by admin'
            )
            db.session.add(payment)

        db.session.commit()

        # ====================== Email ======================
        if mark_paid:
            send_booking_confirmed_email(booking)
        else:
            send_booking_created_email(booking)

        return jsonify({
            'success': True,
            'booking_reference': booking.booking_reference,
            'redirect': url_for('admin.manage_bookings')
        })

    # GET request
    today = date.today().isoformat()
    return render_template('admin/create-booking.html', today=today)




@admin_bp.route('/bookings')
@login_required
@admin_required
def manage_bookings():
    """Manage bookings"""
    status = request.args.get('status', 'all')
    
    query = Booking.query
    if status != 'all':
        query = query.filter_by(status=status)
    
    bookings = query.order_by(Booking.created_at.desc()).all()
    
    return render_template('admin/bookings.html', bookings=bookings, current_status=status)

@admin_bp.route('/bookings/<int:booking_id>/status', methods=['POST'])
@login_required
@admin_required
def update_booking_status(booking_id):
    """Update booking status"""
    booking = Booking.query.get_or_404(booking_id)
    data = request.get_json()
    new_status = data.get('status')
    
    if new_status in ['pending', 'confirmed', 'completed', 'cancelled']:
        booking.status = new_status
        db.session.commit()
        return jsonify({'success': True, 'status': booking.status})
    
    return jsonify({'success': False, 'message': 'Invalid status'}), 400

@admin_bp.route('/services')
@login_required
@admin_required
def manage_services():
    """Manage services"""
    services = Service.query.all()
    return render_template('admin/services.html', services=services)

# ====================== SERVICE REQUESTS (ADMIN) ======================

@admin_bp.route('/service-requests')
@login_required
@admin_required
def service_requests():
    """Manage service requests"""
    status = request.args.get('status', 'pending')
   
    requests = ServiceRequest.query.filter_by(status=status)\
        .order_by(ServiceRequest.created_at.desc()).all()
   
    return render_template('admin/service-requests.html', 
                         requests=requests, 
                         current_status=status)


@admin_bp.route('/service-requests/<int:request_id>/status', methods=['POST'])
@login_required
@admin_required
def update_service_request_status(request_id):
    """Update service request status"""
    service_request = ServiceRequest.query.get_or_404(request_id)
    data = request.get_json()
    new_status = data.get('status')
   
    if new_status in ['pending', 'in_progress', 'completed']:
        old_status = service_request.status
        service_request.status = new_status
        db.session.commit()

        # Optional: Send email to guest when status changes to completed
        if new_status == 'completed' and old_status != 'completed':
            send_service_request_completed_email(service_request)

        return jsonify({'success': True, 'status': service_request.status})
   
    return jsonify({'success': False, 'message': 'Invalid status'}), 400


def send_service_request_completed_email(service_request):
    """Notify guest when service is completed"""
    try:
        subject = f"Your Service Request is Completed - {service_request.service.name}"
        html_body = render_template(
            'emails/guest_service_request_completed.html',
            request=service_request,
            guest=service_request.requester
        )
        msg = Message(
            subject=subject,
            recipients=[service_request.requester.email],
            html=html_body,
            sender=current_app.config['MAIL_DEFAULT_SENDER']
        )
        mail.send(msg)
    except Exception as e:
        current_app.logger.error(f"Failed to send service completed email: {str(e)}")


# ==================== APARTMENT MANAGEMENT ====================

@admin_bp.route('/apartments')
@login_required
@admin_required
def manage_apartments():
    """List all apartments for management"""
    apartment_types = ApartmentType.query.all()
    return render_template('admin/apartments.html', apartment_types=apartment_types)

@admin_bp.route('/apartments/new', methods=['GET', 'POST'])
@login_required
@admin_required
def create_apartment():
    """Create new apartment type"""
    if request.method == 'POST':
        # Support both JSON and form data
        if request.is_json:
            data = request.get_json()
        else:
            data = request.form.to_dict()

        try:
            apartment = ApartmentType(
                name=data.get('name'),
                bedrooms=int(data.get('bedrooms', 0)),
                bathrooms=int(data.get('bathrooms', 0)),
                area_sqm=float(data.get('area_sqm', 0)),
                description=data.get('description', ''),
                base_price=float(data.get('base_price', 0))
            )
            
            db.session.add(apartment)
            db.session.commit()
            
            return jsonify({'success': True, 'apartment_id': apartment.id})
        
        except (ValueError, TypeError) as e:
            return jsonify({'success': False, 'message': 'Invalid data provided'}), 400
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'message': str(e)}), 500

    return render_template('admin/apartment-form.html', apartment=None)

@admin_bp.route('/apartments/<int:apartment_id>', methods=['GET'])
@login_required
@admin_required
def get_apartment(apartment_id):
    """Get single apartment type for editing"""
    apartment = ApartmentType.query.get_or_404(apartment_id)
    
    return jsonify({
        'id': apartment.id,
        'name': apartment.name,
        'bedrooms': apartment.bedrooms,
        'bathrooms': apartment.bathrooms,
        'area_sqm': apartment.area_sqm,
        'base_price': apartment.base_price,
        'description': apartment.description or ''
    })

@admin_bp.route('/apartments/<int:apartment_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_apartment(apartment_id):
    """Edit apartment type"""
    apartment = ApartmentType.query.get_or_404(apartment_id)
    
    if request.method == 'POST':
        data = request.get_json()
        
        apartment.name = data.get('name', apartment.name)
        apartment.bedrooms = int(data.get('bedrooms', apartment.bedrooms))
        apartment.bathrooms = int(data.get('bathrooms', apartment.bathrooms))
        apartment.area_sqm = float(data.get('area_sqm', apartment.area_sqm))
        apartment.description = data.get('description', apartment.description)
        apartment.base_price = float(data.get('base_price', apartment.base_price))
        
        db.session.commit()
        
        return jsonify({'success': True})
    
    return render_template('admin/apartment-form.html', apartment=apartment)

@admin_bp.route('/apartments/<int:apartment_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_apartment(apartment_id):
    """Delete apartment type"""
    apartment = ApartmentType.query.get_or_404(apartment_id)
    
    # Check if apartment has units
    if apartment.units.count() > 0:
        return jsonify({'success': False, 'message': 'Cannot delete apartment with existing units'}), 400
    
    db.session.delete(apartment)
    db.session.commit()
    
    return jsonify({'success': True})


# ==================== UNIT MANAGEMENT ====================

@admin_bp.route('/units')
@login_required
@admin_required
def manage_units():
    units = Unit.query.all()
    return render_template('admin/units.html', units=units)


@admin_bp.route('/units/new', methods=['GET', 'POST'])
@login_required
@admin_required
def create_unit():
    apartment_types = ApartmentType.query.all()

    if request.method == 'POST':
        data = request.get_json()

        unit = Unit(
            unit_number=data.get('unit_number'),
            apartment_type_id=int(data.get('apartment_type_id')),
            floor=int(data.get('floor')),
            view=data.get('view'),
            image_url=data.get('image_url'),           # Google Drive URL
            is_available=data.get('is_available', True)
        )

        db.session.add(unit)
        db.session.commit()

        return jsonify({'success': True, 'unit_id': unit.id})

    return render_template('admin/unit-form.html', unit=None, apartment_types=apartment_types)


@admin_bp.route('/units/<int:unit_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_unit(unit_id):
    unit = Unit.query.get_or_404(unit_id)
    apartment_types = ApartmentType.query.all()

    if request.method == 'POST':
        data = request.get_json()

        unit.unit_number = data.get('unit_number', unit.unit_number)
        unit.apartment_type_id = int(data.get('apartment_type_id', unit.apartment_type_id))
        unit.floor = int(data.get('floor', unit.floor))
        unit.view = data.get('view', unit.view)
        unit.image_url = data.get('image_url', unit.image_url)
        unit.is_available = data.get('is_available', unit.is_available)

        db.session.commit()
        return jsonify({'success': True})

    return render_template('admin/unit-form.html', unit=unit, apartment_types=apartment_types)


@admin_bp.route('/units/<int:unit_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_unit(unit_id):
    unit = Unit.query.get_or_404(unit_id)

    if unit.bookings.count() > 0:
        return jsonify({'success': False, 'message': 'Cannot delete unit with existing bookings'}), 400

    db.session.delete(unit)
    db.session.commit()
    return jsonify({'success': True})


@admin_bp.route('/units/<int:unit_id>/toggle', methods=['POST'])
@login_required
@admin_required
def toggle_unit_availability(unit_id):
    """Toggle unit availability"""
    unit = Unit.query.get_or_404(unit_id)
    unit.is_available = not unit.is_available
    db.session.commit()
    
    return jsonify({'success': True, 'is_available': unit.is_available})



# ==================== GALLERY MANAGEMENT ====================

@admin_bp.route('/units/<int:unit_id>/gallery')
@login_required
@admin_required
def manage_gallery(unit_id):
    unit = Unit.query.get_or_404(unit_id)
    images = UnitImage.query.filter_by(unit_id=unit_id).order_by(UnitImage.display_order).all()
    return render_template('admin/gallery.html', unit=unit, images=images)


@admin_bp.route('/gallery/<int:image_id>', methods=['GET'])
@login_required
@admin_required
def get_gallery_image(image_id):
    """Get single gallery image for editing"""
    image = UnitImage.query.get_or_404(image_id)
    
    return jsonify({
        'id': image.id,
        'image_url': image.image_url,
        'label': image.label or '',
        'description': image.description or '',
        'is_featured': image.is_featured
    })


@admin_bp.route('/units/<int:unit_id>/gallery/add', methods=['POST'])
@login_required
@admin_required
def add_gallery_images(unit_id):
    unit = Unit.query.get_or_404(unit_id)

    if 'file' not in request.files:
        return jsonify({"success": False, "message": "No file uploaded"}), 400

    file = request.files['file']
    if not file or file.filename == '':
        return jsonify({"success": False, "message": "No file selected"}), 400

    # Save file
    filename = secure_filename(file.filename)
    upload_path = os.path.join('uploads', 'units', str(unit_id), filename)
    os.makedirs(os.path.dirname(upload_path), exist_ok=True)
    file.save(upload_path)

    image_url = f"/uploads/units/{unit_id}/{filename}"

    image = UnitImage(
        unit_id=unit_id,
        image_url=image_url,
        label=request.form.get('label', ''),
        description=request.form.get('description', ''),
        is_featured=request.form.get('is_featured') == 'on',
        display_order=UnitImage.query.filter_by(unit_id=unit_id).count()
    )

    db.session.add(image)
    db.session.commit()

    return jsonify({'success': True, 'image_id': image.id})


@admin_bp.route('/gallery/<int:image_id>/edit', methods=['POST'])
@login_required
@admin_required
def edit_gallery_image(image_id):
    image = UnitImage.query.get_or_404(image_id)

    # If new file is uploaded
    if 'file' in request.files and request.files['file'].filename:
        file = request.files['file']
        # Delete old file if exists
        if image.image_url and image.image_url.startswith('/uploads/'):
            old_path = image.image_url.lstrip('/')
            if os.path.exists(old_path):
                try:
                    os.remove(old_path)
                except:
                    pass

        # Save new file
        filename = secure_filename(file.filename)
        upload_path = os.path.join('uploads', 'units', str(image.unit_id), filename)
        os.makedirs(os.path.dirname(upload_path), exist_ok=True)
        file.save(upload_path)

        image.image_url = f"/uploads/units/{image.unit_id}/{filename}"

    image.label = request.form.get('label', image.label)
    image.description = request.form.get('description', image.description)
    image.is_featured = request.form.get('is_featured') == 'on'

    db.session.commit()
    return jsonify({'success': True})


@admin_bp.route('/gallery/<int:image_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_gallery_image(image_id):
    image = UnitImage.query.get_or_404(image_id)

    # Delete physical file
    if image.image_url and image.image_url.startswith('/uploads/'):
        file_path = image.image_url.lstrip('/')
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except:
                pass

    db.session.delete(image)
    db.session.commit()
    return jsonify({'success': True})


@admin_bp.route('/units/<int:unit_id>/gallery/reorder', methods=['POST'])
@login_required
@admin_required
def reorder_gallery(unit_id):
    unit = Unit.query.get_or_404(unit_id)
    data = request.get_json()

    for order, image_id in enumerate(data.get('image_order', [])):
        image = UnitImage.query.get(image_id)
        if image and image.unit_id == unit_id:
            image.display_order = order

    db.session.commit()
    return jsonify({'success': True})