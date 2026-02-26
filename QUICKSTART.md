# Quick Start Guide - Eni's Apartments Platform

## 5-Minute Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Initialize Database
```bash
flask init-db
```
This creates SQLite database with sample data.

### 3. Run Development Server
```bash
python run.py
```
Server runs on `http://localhost:5000`

### 4. Access the App
- **Homepage**: http://localhost:5000/
- **Browse Units**: http://localhost:5000/units
- **Admin Dashboard**: http://localhost:5000/admin/dashboard

### 5. Test Credentials

#### Admin Account
- **Email**: admin@eni.com
- **Password**: admin123

#### Guest Account
- **Email**: guest@eni.com
- **Password**: guest123

## Testing Key Features

### Test 1: Direct Unit Booking (2 min)
1. Go to http://localhost:5000/units
2. Click on any unit (e.g., "Unit 001")
3. In the sidebar, select future dates
4. Click "Check Availability"
5. See instant response with price
6. Click "Proceed to Booking" if available

### Test 2: Guest Booking (3 min)
1. Go to http://localhost:5000/bookings/new (without logging in)
2. Fill in: Email, Phone, First Name, Last Name
3. Select future dates in the main form
4. Click "Complete Booking"
5. See confirmation with guest code
6. Save the guest code
7. Visit `/bookings/guest/[CODE]` to test guest access

### Test 3: Admin Creating Booking (3 min)
1. Login as admin (admin@eni.com / admin123)
2. Go to Admin Dashboard
3. Click "New Booking"
4. Select "New Guest"
5. Fill in guest details
6. Choose a unit and dates
7. Click "Create Booking"
8. See booking reference and guest code

### Test 4: Profile Management (2 min)
1. Login as guest (guest@eni.com / guest123)
2. Go to http://localhost:5000/auth/profile
3. Edit name or phone
4. Click "Save Changes"
5. Change password
6. Try new password on next login

## Common Commands

### Database Operations
```bash
# Initialize fresh database
flask init-db

# Reset database (deletes all data)
rm instance/eni.db && flask init-db

# Create migration
flask db migrate -m "description"

# Apply migration
flask db upgrade
```

### Development
```bash
# Run with debug mode
python run.py

# Run with custom port
export FLASK_ENV=development
export FLASK_PORT=5001
python run.py
```

### Production
```bash
# Create .env file with:
# FLASK_ENV=production
# DATABASE_URL=postgresql://...

# Run with Gunicorn
gunicorn -w 4 run:app
```

## Project Structure Quick Reference

```
app/
├── __init__.py           # App factory
├── models.py             # Database models
├── main/routes.py        # Public pages
├── auth/routes.py        # Login/register
├── bookings/routes.py    # Booking flows
├── admin/routes.py       # Admin panel
├── api/routes.py         # REST API
└── templates/            # HTML templates

config.py                # Configuration
run.py                   # Entry point
```

## Key URLs

### Public
- `/` - Homepage
- `/units` - All units
- `/units/<id>` - Unit details
- `/services` - Services page
- `/bookings/availability` - Search units
- `/bookings/new` - Create booking

### Auth Required
- `/auth/login` - Login
- `/auth/register` - Register
- `/auth/profile` - User profile
- `/guest/dashboard` - My bookings

### Admin Only
- `/admin/dashboard` - Overview
- `/admin/units` - Manage units
- `/admin/bookings` - Manage bookings
- `/admin/create-booking` - Create for guest

### API
- `/api/units` - Get all units
- `/api/availability?unit_id=1&check_in=...&check_out=...` - Check availability

## Troubleshooting

### Port Already in Use
```bash
# Change port
export FLASK_PORT=5001
python run.py
```

### Database Error
```bash
# Reset database
rm instance/eni.db
flask init-db
```

### Import Errors
```bash
# Reinstall dependencies
pip install --upgrade -r requirements.txt
```

### Template Not Found Error
```bash
# Run from project root
cd /path/to/project
python run.py
```

## Making Changes

### Adding a New Route
1. Find appropriate blueprint file (`app/auth/routes.py`, etc.)
2. Add route with `@blueprint.route()`
3. Create template in `app/templates/`
4. Test at http://localhost:5000/your-route

### Adding a New Field to Database
1. Update model in `app/models.py`
2. Create migration: `flask db migrate`
3. Apply migration: `flask db upgrade`
4. Update templates to use new field

### Styling Changes
1. Edit HTML template in `app/templates/`
2. Use Tailwind CSS classes
3. No CSS compilation needed
4. Changes appear instantly on refresh

### JavaScript Changes
1. Edit JavaScript in template `{% block extra_js %}`
2. Fetch API calls to Flask routes
3. Changes appear instantly on refresh

## Testing Bookings

### Test Data
The `flask init-db` command creates:
- 4 units (Unit 001 - Unit 004)
- 2 users (admin, guest)
- 7 essential services
- 5 optional services
- Sample bookings

### Create Test Booking Manually
1. Login as guest
2. Go to any unit page
3. Select future dates
4. Check availability
5. Complete booking form
6. Should redirect to confirmation

### Check Booking in Database
```python
from app import db
from app.models import Booking

# Open Python shell
python

# Inside shell:
from app import create_app, db
from app.models import Booking
app = create_app()
with app.app_context():
    bookings = Booking.query.all()
    for b in bookings:
        print(f"{b.booking_reference}: {b.guest.first_name} {b.guest.last_name}")
```

## API Testing with cURL

### Check Availability
```bash
curl "http://localhost:5000/api/availability?unit_id=1&check_in=2024-02-15&check_out=2024-02-20"
```

### Get All Units
```bash
curl http://localhost:5000/api/units
```

### Create Booking (JSON)
```bash
curl -X POST http://localhost:5000/bookings/new \
  -H "Content-Type: application/json" \
  -d '{
    "unit_id": 1,
    "check_in": "2024-02-15T00:00:00",
    "check_out": "2024-02-20T00:00:00",
    "num_guests": 2,
    "guest_email": "test@example.com",
    "guest_first_name": "John",
    "guest_last_name": "Doe",
    "guest_phone": "+234 800 000 0000"
  }'
```

## Performance Tips

1. **Database**: SQLite fine for development, use PostgreSQL for production
2. **Debug Mode**: Only use `FLASK_DEBUG=1` during development
3. **Static Files**: Serve via CDN in production
4. **Caching**: Browser cache helps with repeated access
5. **Images**: Optimize images for web (compress, use appropriate size)

## Deployment Checklist

- [ ] Set `FLASK_ENV=production`
- [ ] Set strong `SECRET_KEY`
- [ ] Use PostgreSQL database
- [ ] Set `PREFERRED_URL_SCHEME=https`
- [ ] Configure email service (future)
- [ ] Set up error logging
- [ ] Test all features
- [ ] Check responsive design
- [ ] Test on different browsers
- [ ] Set up SSL certificate

## Next Steps

1. **Explore the Code**: Review `app/models.py` for data structure
2. **Customize**: Update brand colors, text, services
3. **Test Features**: Use testing checklist above
4. **Deploy**: Follow deployment checklist
5. **Monitor**: Watch logs for errors

## Need Help?

1. Check `README.md` for full documentation
2. Review `UPDATES.md` for feature details
3. Check `ROUTES.md` for API reference
4. Look at `ARCHITECTURE.md` for system design
5. Review error messages in browser console

## Quick Customization

### Change Brand Colors
Edit `app/templates/base.html`:
```html
<!-- Find color references -->
<div class="text-[#E96C40]">  <!-- Change this hex color -->
```

### Change Site Title
Edit `app/__init__.py`:
```python
# Change "Eni's Apartments" to your name
```

### Add New Service
1. Edit `app/cli.py` in `init_db()` function
2. Add new Service record
3. Run `flask init-db` or add via admin panel

### Change Pricing
Edit `app/cli.py`:
```python
# Find base_price values and update
apartment = ApartmentType(base_price=YOUR_PRICE)
```

## Development Tips

- Use browser DevTools (F12) to debug JavaScript
- Check Flask logs for backend errors
- Use `/api/` endpoints to test data
- Test with different dates/scenarios
- Check database directly if needed

---

**Ready to go!** Start with Test 1 above.
