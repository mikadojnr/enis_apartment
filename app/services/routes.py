from flask import render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from app.services import services_bp
from app import db
from app.models import Service, ServiceRequest, Booking

@services_bp.route('/request', methods=['GET', 'POST'])
@login_required
def request_service():
    """Request a service"""
    if request.method == 'POST':
        data = request.get_json()
        service_id = data.get('service_id')
        booking_id = data.get('booking_id')
        notes = data.get('notes')
        
        # Verify booking belongs to user
        booking = Booking.query.get_or_404(booking_id)
        if booking.user_id != current_user.id:
            return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        
        service_request = ServiceRequest(
            service_id=service_id,
            booking_id=booking_id,
            user_id=current_user.id,
            notes=notes,
            status='pending'
        )
        
        db.session.add(service_request)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Service request submitted'})
    
    services = Service.query.filter_by(is_active=True).all()
    bookings = current_user.bookings.filter_by(status='confirmed').all()
    
    return render_template('services/request.html', services=services, bookings=bookings)

@services_bp.route('/requests')
@login_required
def my_requests():
    """View my service requests"""
    requests = current_user.service_requests.all()
    return render_template('services/my-requests.html', requests=requests)

@services_bp.route('/<int:request_id>/cancel', methods=['POST'])
@login_required
def cancel_service_request(request_id):
    """Cancel service request"""
    service_request = ServiceRequest.query.get_or_404(request_id)
    
    if service_request.user_id != current_user.id:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    if service_request.status == 'completed':
        return jsonify({'success': False, 'message': 'Cannot cancel completed request'}), 400
    
    service_request.status = 'cancelled'
    db.session.commit()
    
    flash('Service request cancelled', 'info')
    return redirect(url_for('services.my_requests'))
