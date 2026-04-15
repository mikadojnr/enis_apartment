from app import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from enum import Enum

class User(UserMixin, db.Model):
    """User model for guests and admins"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(120), nullable=False)
    last_name = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20))
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    bookings = db.relationship('Booking', backref='user', lazy='dynamic')
    service_requests = db.relationship('ServiceRequest', backref='requester', lazy='dynamic')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.email}>'

@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))

apartment_type_services = db.Table('apartment_type_services',
    db.Column('apartment_type_id', db.Integer, db.ForeignKey('apartment_types.id'), primary_key=True),
    db.Column('service_id', db.Integer, db.ForeignKey('services.id'), primary_key=True)
)

class ApartmentType(db.Model):
    """Apartment type (e.g., 2-bedroom)"""
    __tablename__ = 'apartment_types'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    bedrooms = db.Column(db.Integer, nullable=False)
    bathrooms = db.Column(db.Integer, nullable=False)
    area_sqm = db.Column(db.Float, nullable=False)
    base_price = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text)

    # ✅ FIXED HERE
    amenities = db.Column(db.JSON, default=list)

    rating = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    units = db.relationship('Unit', backref='apartment_type', lazy='dynamic')
    services = db.relationship(
        'Service',
        secondary=apartment_type_services,
        lazy='subquery',
        backref=db.backref('apartment_types', lazy=True)
    )
    
    def __repr__(self):
        return f'<ApartmentType {self.name}>'
      
class Unit(db.Model):
    """Individual apartment unit"""
    __tablename__ = 'units'
    
    id = db.Column(db.Integer, primary_key=True)
    unit_number = db.Column(db.String(50), unique=True, nullable=False, index=True)
    apartment_type_id = db.Column(db.Integer, db.ForeignKey('apartment_types.id'), nullable=False)
    floor = db.Column(db.Integer, nullable=False)
    view = db.Column(db.String(120))  # e.g., "City View", "Garden View"
    image_url = db.Column(db.String(255))
    is_available = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    bookings = db.relationship('Booking', backref='unit', lazy='dynamic')
    gallery_images = db.relationship('UnitImage', backref='unit', lazy='dynamic', cascade='all, delete-orphan')
    service_requests = db.relationship('ServiceRequest', backref='unit', lazy='dynamic')
    
    def __repr__(self):
        return f'<Unit {self.unit_number}>'
    
class UnitImage(db.Model):
    """Gallery images for apartment units"""
    __tablename__ = 'unit_images'
    
    id = db.Column(db.Integer, primary_key=True)
    unit_id = db.Column(db.Integer, db.ForeignKey('units.id'), nullable=False, index=True)
    image_url = db.Column(db.String(255), nullable=False)
    label = db.Column(db.String(120))  # e.g., "Living Room", "Master Bedroom", "Kitchen"
    description = db.Column(db.Text)
    display_order = db.Column(db.Integer, default=0)  # For custom ordering
    is_featured = db.Column(db.Boolean, default=False)  # Feature image on unit list
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<UnitImage {self.label} - {self.unit.unit_number}>'

# Association table for Booking ↔ Service (addons)
booking_addons = db.Table('booking_addons',
    db.Column('booking_id', db.Integer, db.ForeignKey('bookings.id'), primary_key=True),
    db.Column('service_id',  db.Integer, db.ForeignKey('services.id'),  primary_key=True),
    db.Column('quantity',    db.Integer, default=1),   # optional – if you later want qty
)
       
class Booking(db.Model):
    """Booking/reservation"""
    __tablename__ = 'bookings'
    
    id = db.Column(db.Integer, primary_key=True)
    booking_reference = db.Column(db.String(50), unique=True, nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    unit_id = db.Column(db.Integer, db.ForeignKey('units.id'), nullable=False)

    first_name       = db.Column(db.String(120), nullable=False)
    last_name        = db.Column(db.String(120), nullable=False)
    email            = db.Column(db.String(120), nullable=False, index=True)
    phone            = db.Column(db.String(30), nullable=False)
    id_type          = db.Column(db.String(50))           # passport, nin, drivers_license
    id_upload_url = db.Column(db.String(255), nullable=True)  # path/URL to uploaded ID doc
    num_adults       = db.Column(db.Integer, default=0)
    
    check_in_date = db.Column(db.DateTime, nullable=False)
    check_out_date = db.Column(db.DateTime, nullable=False)
    number_of_guests = db.Column(db.Integer, nullable=False)
    num_children = db.Column(db.Integer, default=0)

    expires_at = db.Column(db.DateTime, nullable=True)  # null = no expiry or already paid/completed
    
    status = db.Column(db.String(50), default='pending')  # pending, confirmed, completed, cancelled
    total_price = db.Column(db.Float, nullable=False)
    paid = db.Column(db.Boolean, default=False)
    
    # Guest booking code - for unauthenticated guest access
    guest_code = db.Column(db.String(20), unique=True, nullable=True, index=True)
    is_guest_booking = db.Column(db.Boolean, default=False)  # True if booked by admin for guest
    guest_email = db.Column(db.String(120))  # Guest email if not registered user
    guest_phone = db.Column(db.String(20))
    
    special_requests = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    service_requests = db.relationship('ServiceRequest', backref='booking', lazy='dynamic')
    # user = db.relationship('User', backref=db.backref('bookings', lazy='dynamic'))

    addons = db.relationship(
        'Service',
        secondary=booking_addons,
        lazy='subquery',
        backref=db.backref('bookings', lazy=True)
    )
    
    def __repr__(self):
        return f'<Booking {self.booking_reference}>'  

class VerifiedID(db.Model):
    """Stores successfully verified IDs (both logged-in and guest users)"""
    __tablename__ = 'verified_ids'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    email = db.Column(db.String(120), nullable=True, index=True)   # for guests
    id_type = db.Column(db.String(50), nullable=False)             # nin, passport, drivers_license
    id_number = db.Column(db.String(100), nullable=False)
    full_name = db.Column(db.String(200))
    date_of_birth = db.Column(db.Date, nullable=True)
    verification_id = db.Column(db.String(100))                    # from IDAnalyzer/DocuPass
    document_url = db.Column(db.String(255))
    selfie_url = db.Column(db.String(255), nullable=True)
    is_verified = db.Column(db.Boolean, default=True)
    verified_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=True)             # optional: re-verify after 1 year

    user = db.relationship('User', backref=db.backref('verified_ids', lazy=True))

    def __repr__(self):
        return f'<VerifiedID {self.id_type} - {self.email or self.user_id}>'
 
class Service(db.Model):
    """Available services"""
    __tablename__ = 'services'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False, unique=True)
    category = db.Column(db.String(50), nullable=False)  # essential or optional
    description = db.Column(db.Text)
    price = db.Column(db.Float, default=0)  # 0 for essential services
    pricing_type = db.Column(db.String(50))  # e.g., 'per_person_per_day', 'per_stay', 'per_trip'
    icon = db.Column(db.String(50))  # Emoji or icon code
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    service_requests = db.relationship('ServiceRequest', backref='service', lazy='dynamic')
    
    def __repr__(self):
        return f'<Service {self.name}>'
    
class ServiceRequest(db.Model):
    """Service requests made by guests"""
    __tablename__ = 'service_requests'
    
    id = db.Column(db.Integer, primary_key=True)
    service_id = db.Column(db.Integer, db.ForeignKey('services.id'), nullable=False)
    booking_id = db.Column(db.Integer, db.ForeignKey('bookings.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    unit_id = db.Column(db.Integer, db.ForeignKey('units.id'), nullable=False)
    
    status = db.Column(db.String(50), default='pending')  # pending, in_progress, completed
    notes = db.Column(db.Text)

    payment_reference = db.Column(db.String(100), nullable=True)
    paid = db.Column(db.Boolean, default=False)
    paid_at = db.Column(db.DateTime, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<ServiceRequest {self.id}>'
    
class Payment(db.Model):
    """Track payments made for bookings"""
    __tablename__ = 'payments'

    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('bookings.id'), nullable=False)
    payment_reference = db.Column(db.String(100), unique=True, nullable=False, index=True)  # from Paystack or internal
    # amount = db.Column(db.Float, nullable=False)
    amount = db.Column(db.Numeric(10,2), nullable=False)
    currency = db.Column(db.String(10), default='NGN')
    status = db.Column(db.String(50), default='pending')  # pending, success, failed, refunded
    payment_method = db.Column(db.String(50))  # card, bank, ussd, etc.
    transaction_date = db.Column(db.DateTime, default=datetime.utcnow)
    gateway_response = db.Column(db.Text)  # raw response from Paystack
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    booking = db.relationship('Booking', backref='payments', lazy='select')

    def __repr__(self):
        return f'<Payment {self.payment_reference} for Booking {self.booking_id}>'