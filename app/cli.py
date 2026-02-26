import click
from app import db
from app.models import ApartmentType, Unit, Service, User

def register_cli(app):
    """Register CLI commands"""
    
    @app.cli.command()
    def init_db():
        """Initialize database with sample data"""
        click.echo('Initializing database...')
        
        # Create apartment types
        apt_2br = ApartmentType(
            name='2 Bedroom Superior',
            bedrooms=2,
            bathrooms=2,
            area_sqm=95,
            description='Spacious 2-bedroom apartment with modern amenities',
            base_price=150.0
        )
        
        db.session.add(apt_2br)
        db.session.commit()
        
        # Create units
        units_data = [
            ('UNIT-A1', 'The Ashford', 3, 'City View', 'https://images.unsplash.com/photo-1522708323590-d24dbb6b0267?w=800&q=80'),
            ('UNIT-B2', 'The Berkeley', 2, 'Garden View', 'https://images.unsplash.com/photo-1560448204-e02f11c3d0e2?w=800&q=80'),
            ('UNIT-C3', 'The Cambridge', 4, 'Street View', 'https://images.unsplash.com/photo-1493809842364-78817add7ffb?w=800&q=80'),
            ('UNIT-D4', 'The Duchess', 1, 'Pool View', 'https://images.unsplash.com/photo-1502672260266-1c1ef2d93688?w=800&q=80'),
        ]
        
        for unit_num, name, floor, view, img in units_data:
            unit = Unit(
                unit_number=unit_num,
                apartment_type_id=apt_2br.id,
                floor=floor,
                view=view,
                image_url=img,
                is_available=True
            )
            db.session.add(unit)
        
        db.session.commit()
        
        # Create services
        essential_services = [
            ('24/7 Security', 'essential', 'Round-the-clock surveillance', 0),
            ('Electricity Supply', 'essential', 'Uninterrupted power supply', 0),
            ('Water Supply', 'essential', 'Clean water supply 24/7', 0),
            ('Housekeeping', 'essential', 'Regular cleaning services', 0),
            ('Furnished Apartments', 'essential', 'Fully furnished units', 0),
            ('Maintenance Services', 'essential', 'Prompt maintenance', 0),
            ('Parking Space', 'essential', 'Secure covered parking', 0),
        ]
        
        optional_services = [
            ('Laundry & Dry Cleaning', 'optional', 'Professional laundry services', 15),
            ('Gym & Fitness Facilities', 'optional', 'Modern gym equipment', 25),
            ('Concierge Services', 'optional', '24/7 concierge assistance', 20),
            ('Airport Shuttle', 'optional', 'Transportation service', 35),
            ('Pet-Friendly Options', 'optional', 'Pet accommodation', 10),
        ]
        
        for name, category, desc, price in essential_services + optional_services:
            service = Service(
                name=name,
                category=category,
                description=desc,
                price=price,
                is_active=True
            )
            db.session.add(service)
        
        db.session.commit()
        
        # Create admin user
        admin = User(
            email='admin@eniapartments.com',
            first_name='Admin',
            last_name='User',
            phone='+234-800-000-0000',
            is_admin=True
        )
        admin.set_password('admin123')
        
        db.session.add(admin)
        db.session.commit()
        
        click.echo('Database initialized successfully!')
        click.echo('Admin email: admin@eniapartments.com')
        click.echo('Admin password: admin123')
