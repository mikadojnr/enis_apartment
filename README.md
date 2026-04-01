# Eni's Apartments - Luxury Serviced Apartment Platform

A full-stack web application for managing luxury serviced apartments in Abuja, Nigeria. Built with Python Flask, SQLAlchemy, and modern frontend technologies.

## Project Overview

Eni's Apartments is a complete booking and property management system featuring:
- **4 luxury 2-bedroom units** with unique features
- **7 essential services** included with every stay
- **5 optional premium services** available for additional fees
- **Full booking management system** with availability checking
- **Guest dashboard** for managing reservations and service requests
- **Admin dashboard** for property management
- **Responsive design** using Tailwind CSS 4 and vanilla JavaScript

### Brand Colors
- Primary: `#632A89` (Deep Purple)
- Accent: `#E96C40` (Burnt Orange)
- Secondary: `#94CA3E` (Lime Green)

## Tech Stack

### Backend
- **Framework**: Flask 3.0
- **Database**: SQLAlchemy (SQLite for development, PostgreSQL recommended for production)
- **Authentication**: Flask-Login with custom user models
- **Forms**: Flask-WTF with validation
- **Migrations**: Flask-Migrate
- **CORS**: Flask-CORS for API requests
- **Password Hashing**: Werkzeug

### Frontend
- **Markup**: HTML5 with Jinja2 templating
- **Styling**: Tailwind CSS 4
- **JavaScript**: Vanilla ES6+
- **Icons**: Unicode and emoji (easily replaceable with icon libraries)

## Project Structure

```
app/
├── __init__.py              # App factory and extensions
├── models.py                # Database models
├── cli.py                   # CLI commands for database initialization
├── main/                    # Public pages blueprint
│   ├── __init__.py
│   └── routes.py
├── auth/                    # Authentication blueprint
│   ├── __init__.py
│   ├── routes.py
│   └── forms.py
├── bookings/                # Booking management blueprint
│   ├── __init__.py
│   └── routes.py
├── services/                # Service requests blueprint
│   ├── __init__.py
│   └── routes.py
├── admin/                   # Admin panel blueprint
│   ├── __init__.py
│   └── routes.py
├── api/                     # REST API blueprint
│   ├── __init__.py
│   └── routes.py
└── templates/               # HTML templates
    ├── base.html
    ├── index.html
    ├── units.html
    ├── unit-details.html
    ├── services.html
    ├── about.html
    ├── contact.html
    ├── auth/
    ├── bookings/
    ├── admin/
    └── guest/

config.py                     # Configuration management
run.py                        # Application entry point
requirements.txt              # Python dependencies
```

## New Features (Latest Update)

### Smart Direct Booking from Unit Details
- **Problem Solved**: Users no longer get redirected to a generic availability search after selecting a unit
- **Solution**: Integrated availability check directly on unit-details page
- **How it Works**: 
  1. Guest selects check-in/check-out dates on unit page
  2. System shows instant availability status for that specific unit
  3. If available, price breakdown displays with booking confirmation button
  4. If not available, suggests searching other units
  5. Seamless redirect to `/bookings/new` with pre-filled unit and dates

### Guest Booking Codes
- **Feature**: Unauthenticated guests can access their bookings with unique codes
- **Use Case**: Guests without registered accounts can still view their booking details
- **How it Works**:
  1. Admin or system generates 6-character unique code (e.g., "ABC123")
  2. Code is sent to guest email after booking confirmation
  3. Guest visits `/bookings/guest/[CODE]` to view booking
  4. Code is valid only during booking dates for security
  5. Guests can view details, request services, get support contact info

### Admin Create Booking Feature
- **Purpose**: Admins can book units directly for guest clients
- **Scenarios**: 
  - Corporate clients requesting bookings
  - Phone/email bookings
  - Negotiated rates or special arrangements
  - Walk-in customers without online access
- **Process**:
  1. Admin navigates to `/admin/create-booking`
  2. Selects guest (registered user or creates new guest profile)
  3. Chooses unit, dates, number of guests
  4. Adds special requests and notes
  5. Marks as paid if needed
  6. System generates booking reference and guest code automatically
  7. Guest receives email with booking details and access code

### Guest Account Features
- **Profile Page** (`/auth/profile`): 
  - Update personal information
  - Change password
  - View account creation date and status
  - See booking statistics (total, completed, upcoming)
  - Quick actions for new booking or viewing bookings
- **Password Security**: Passwords must be 8+ characters
- **Email Verification**: Email addresses are unique per account

## Key Features

### Public Pages
1. **Landing Page** - Hero section, unit showcase, services overview, CTA
2. **Units Page** - Browse all apartments with filtering and availability
3. **Unit Details** - Full details, amenities, pricing, instant availability check & direct booking
4. **Services** - Essential and optional services with descriptions
5. **About** - Property story, team, standards, location info
6. **Contact** - Contact form, FAQ, support details

### Smart Booking Flow
1. **Direct Unit Booking** - Check availability directly on unit-details page without redirect
2. **Instant Feedback** - Shows availability status inline with price breakdown
3. **Streamlined New Booking** - `/bookings/new` page with guest info form
4. **Booking Confirmation** - Detailed confirmation page with booking reference
5. **Guest Access Codes** - Unique code for unauthenticated guests to access booking details
6. **Booking Management** - View, modify, cancel reservations

### Guest Features
1. **User Dashboard** - View all bookings, service requests, and account status
2. **Profile Management** - Update profile info, change password
3. **Service Requests** - Request housekeeping, laundry, maintenance, concierge, etc.
4. **Guest Code Access** - Guests without accounts can access bookings via unique code
5. **Booking Status Tracking** - Real-time status updates on all reservations

### Admin Features  
1. **Admin Dashboard** - Overview of bookings, units, users, and pending service requests
2. **Unit Management** - Add, edit, manage apartment units and availability
3. **Booking Management** - View all bookings, update status, manage reservations
4. **Create Booking for Guests** - Admin can create and manage bookings for client guests
5. **Guest Information** - Store guest emails and phone numbers for non-registered users
6. **Service Request Management** - Process and track all guest service requests
7. **Guest Code Generation** - Automatic codes for guest-only bookings
8. **Service Management** - Configure essential and optional services
3. **Profile Management** - Update personal information
4. **Booking History** - Track all past and current stays

### Admin Features
1. **Dashboard** - Overview of bookings, units, users, pending requests
2. **Unit Management** - Toggle availability, manage unit details
3. **Booking Management** - Process, confirm, and complete bookings
4. **Service Requests** - Track and manage guest service requests
5. **Analytics** - View booking trends and guest statistics

## Database Models

### User
- Email (unique)
- Password hash
- Name (first, last)
- Phone
- Admin flag
- Timestamps

### ApartmentType
- Name (e.g., "2 Bedroom Superior")
- Bedrooms, bathrooms, area
- Description
- Base price per day

### Unit
- Unit number (unique)
- Apartment type reference
- Floor, view
- Image URL
- Availability status

### Booking
- Booking reference (unique)
- Guest (user) and unit references
- Check-in/check-out dates
- Guest count
- Total price, payment status
- Status (pending, confirmed, completed, cancelled)

### Service
- Name (unique)
- Category (essential/optional)
- Description
- Price (0 for essential services)
- Active status

### ServiceRequest
- Service and booking references
- Status (pending, in_progress, completed)
- Notes/special requests
- Timestamps

## Setup Instructions

### 1. Clone and Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Environment Configuration

Create a `.env` file in the root directory:

```env
FLASK_APP=run.py
FLASK_ENV=development
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///eni_apartments.db
```

For production, use PostgreSQL:
```env
DATABASE_URL=postgresql://user:password@localhost:5432/eni_apartments
```

### 3. Initialize Database

```bash
# Create tables and add sample data
flask init-db
```

This creates:
- 4 apartment units (UNIT-A1, UNIT-B2, UNIT-C3, UNIT-D4)
- Admin user: email `admin@eniapartments.com`, password `admin123`
- All essential and optional services

### 4. Run Development Server

```bash
python run.py
```

Server runs at `http://localhost:5000`

## Database Migrations

When modifying models:

```bash
# Generate migration
flask db migrate -m "Description of changes"

# Apply migration
flask db upgrade

# Rollback if needed
flask db downgrade
```

## API Endpoints

All API endpoints are prefixed with `/api/`

### Units
- `GET /api/units` - Get all units
- `GET /api/units/<id>` - Get unit details

### Services
- `GET /api/services` - Get all active services

### Availability
- `GET /api/availability?unit_id=1&check_in=2024-02-15&check_out=2024-02-17` - Check availability

### Pricing
- `GET /api/price?unit_id=1&check_in=2024-02-15&check_out=2024-02-17` - Calculate booking price

## Authentication

User login is required for:
- Making bookings
- Requesting services
- Accessing guest dashboard

Admin access required for:
- Admin dashboard
- Unit management
- Booking management
- Service request handling

**Default Admin Credentials (CHANGE IN PRODUCTION)**
- Email: `admin@eniapartments.com`
- Password: `admin123`

## Forms & Validation

### Login Form
- Email (required, valid format)
- Password (required)
- Remember me (optional)

### Registration Form
- Email (required, unique, valid format)
- First/Last Name (required, min 2 chars)
- Phone (required)
- Password (required, min 6 chars)
- Password confirmation (must match)

## Security Best Practices

✅ Implemented:
- Password hashing with Werkzeug
- CSRF protection with Flask-WTF
- Secure session cookies (HttpOnly, Secure, SameSite)
- SQL parameterization via SQLAlchemy ORM
- Input validation on all forms
- Authentication required for sensitive operations
- Admin-only access controls

⚠️ Production TODO:
- Update `SECRET_KEY` to random secure value
- Enable `SESSION_COOKIE_SECURE = True` (requires HTTPS)
- Use PostgreSQL instead of SQLite
- Implement rate limiting
- Add email verification for registrations
- Implement password reset flow
- Enable HTTPS/SSL certificates

## Customization

### Adding More Units
Edit `/app/cli.py` in the `init_db()` function to add more unit definitions.

### Changing Pricing
Modify the `base_price` in the `ApartmentType` model and update unit prices in the initialization script.

### Adding Services
Add new services in the `init_db()` function or via admin interface.

### Styling
Tailwind CSS configuration can be modified in `tailwind.config.ts` (if using Tailwind's build system) or by updating color classes throughout templates.

## Deployment

### Vercel (Recommended for Frontend)
The frontend (static pages and templates) can be deployed to Vercel:

```bash
vercel deploy
```

### PythonAnywhere / Heroku
For Flask backend deployment:

```bash
# Create Procfile
echo "web: gunicorn run:app" > Procfile

# Deploy to Heroku
heroku create eni-apartments
heroku config:set SECRET_KEY=your-production-secret-key
heroku config:set DATABASE_URL=your-postgres-url
git push heroku main
heroku run flask db upgrade
```

## Troubleshooting

### Database Errors
```bash
# Reset database (development only)
rm eni_apartments.db
flask init-db
```

### CSRF Token Errors
Ensure Flask-WTF is properly configured and form includes `{{ form.hidden_tag() }}`

### Module Not Found
```bash
pip install --upgrade -r requirements.txt
```

## Future Enhancements

- [ ] Payment integration (Stripe, Paystack)
- [ ] Email notifications for bookings
- [ ] SMS alerts for service requests
- [ ] Guest reviews and ratings
- [ ] Cleaning checklist and management
- [ ] Dynamic pricing based on demand
- [ ] Multi-language support
- [ ] Mobile app (React Native/Flutter)
- [ ] Analytics and reporting dashboard
- [ ] Calendar integration
- [ ] Pet policy management
- [ ] Membership/loyalty program

## License

This project is proprietary software. All rights reserved.

## Contact

- **Phone**: +234-911-8818881
- **Email**: stay@enisapartment.com
- **Location**: Abuja, Federal Capital Territory, Nigeria

---

**Eni's Apartments Limited**
