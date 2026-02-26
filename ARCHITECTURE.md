# Eni's Apartments - Architecture & Data Flow

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      CLIENT LAYER                            │
│  HTML Templates + Vanilla JS + Tailwind CSS 4                │
└─────────────────────────────────────────────────────────────┘
                             ↕
┌─────────────────────────────────────────────────────────────┐
│                  FLASK APPLICATION LAYER                     │
│  ┌────────────────┐ ┌────────────────┐ ┌────────────────┐  │
│  │  Auth Routes   │ │ Booking Routes │ │  Admin Routes  │  │
│  └────────────────┘ └────────────────┘ └────────────────┘  │
│  ┌────────────────┐ ┌────────────────┐ ┌────────────────┐  │
│  │ Main Routes    │ │ Service Routes │ │  API Routes    │  │
│  └────────────────┘ └────────────────┘ └────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                             ↕
┌─────────────────────────────────────────────────────────────┐
│                   DATABASE LAYER                             │
│        SQLAlchemy ORM + SQLite/PostgreSQL                    │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Users │ Bookings │ Units │ Services │ Requests     │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## Data Models

### User Model
```
User
├── id (Primary Key)
├── email (Unique)
├── password_hash
├── first_name
├── last_name
├── phone
├── is_admin
├── created_at
├── updated_at
└── Relationships:
    ├── bookings (One-to-Many)
    └── service_requests (One-to-Many)
```

### Booking Model
```
Booking
├── id (Primary Key)
├── booking_reference (Unique) - "ENI-XXXXXX"
├── user_id (Foreign Key)
├── unit_id (Foreign Key)
├── check_in_date
├── check_out_date
├── number_of_guests
├── status - pending/confirmed/completed/cancelled
├── total_price
├── paid
├── special_requests
├── guest_code (Unique) - "XXXXXX" ← NEW
├── is_guest_booking ← NEW
├── guest_email ← NEW
├── guest_phone ← NEW
├── created_at
├── updated_at
└── Relationships:
    ├── guest (User)
    ├── unit (Unit)
    └── service_requests (One-to-Many)
```

### Unit Model
```
Unit
├── id (Primary Key)
├── unit_number (Unique)
├── apartment_type_id (Foreign Key)
├── floor
├── view
├── image_url
├── is_available
├── created_at
└── Relationships:
    ├── apartment_type (ApartmentType)
    └── bookings (One-to-Many)
```

### ApartmentType Model
```
ApartmentType
├── id (Primary Key)
├── name - "2 Bedroom", "3 Bedroom", etc.
├── bedrooms
├── bathrooms
├── area_sqm
├── description
├── base_price
├── created_at
└── Relationships:
    └── units (One-to-Many)
```

### Service Model
```
Service
├── id (Primary Key)
├── name (Unique)
├── category - essential/optional
├── description
├── price - 0 for essential
├── is_active
├── created_at
└── Relationships:
    └── service_requests (One-to-Many)
```

### ServiceRequest Model
```
ServiceRequest
├── id (Primary Key)
├── service_id (Foreign Key)
├── booking_id (Foreign Key)
├── user_id (Foreign Key)
├── status - pending/in_progress/completed
├── notes
├── created_at
├── updated_at
└── Relationships:
    ├── service (Service)
    ├── booking (Booking)
    └── requester (User)
```

## Request/Response Flow

### Direct Booking Flow (Unit Details Page)

```
1. User on /units/<id> Page
   │
   ├─→ Fills dates in sidebar form
   │
   ├─→ Clicks "Check Availability"
   │
   ├─→ JavaScript prepares data:
   │   {
   │     unit_id: 1,
   │     check_in: "2024-01-15",
   │     check_out: "2024-01-20"
   │   }
   │
   ├─→ POST to /api/availability
   │
   ├─→ Backend checks Booking table:
   │   SELECT * FROM bookings
   │   WHERE unit_id = 1
   │   AND (check_in_date < check_out OR check_out_date > check_in)
   │
   ├─→ Returns:
   │   {
   │     is_available: true,
   │     unit_number: "Unit 001",
   │     total_price: 25000
   │   }
   │
   ├─→ JavaScript shows:
   │   - Green checkmark "Available!"
   │   - Price breakdown
   │   - "Proceed to Booking" button
   │
   └─→ User clicks button
       └─→ Redirect to /bookings/new?unit_id=1&check_in=2024-01-15&check_out=2024-01-20
```

### Create Booking Flow (Registered User)

```
1. User fills /bookings/new form
   │
   ├─→ User logged in (pre-filled name/email)
   │
   ├─→ Fills dates, guests, special requests
   │
   ├─→ Clicks "Complete Booking"
   │
   ├─→ JavaScript validates:
   │   - Check-in after today
   │   - Check-out after check-in
   │   - Terms accepted
   │
   ├─→ POST /bookings/new with:
   │   {
   │     unit_id: 1,
   │     check_in: "2024-01-15T00:00:00",
   │     check_out: "2024-01-20T00:00:00",
   │     num_guests: 2,
   │     special_requests: "..."
   │   }
   │
   ├─→ Backend:
   │   ├─ Gets Unit (base_price = 5000)
   │   ├─ Calculates days = 5
   │   ├─ Calculates total_price = 5000 * 5 = 25000
   │   ├─ Generates booking_reference = "ENI-ABC12345"
   │   ├─ Creates Booking record:
   │   │  user_id = current_user.id
   │   │  unit_id = 1
   │   │  status = 'pending'
   │   │  total_price = 25000
   │   └─ Saves to database
   │
   ├─→ Returns:
   │   {
   │     success: true,
   │     booking_id: 42
   │   }
   │
   └─→ Redirect to /bookings/42/confirmation
       └─→ Display booking details, reference, instructions
```

### Guest Booking Flow (No Account)

```
1. Same as registered user up to booking creation
   │
   ├─→ User NOT logged in
   │
   ├─→ Fills email, phone, name in booking form
   │
   ├─→ Backend:
   │   ├─ Checks if email exists
   │   ├─ If not:
   │   │  ├─ Create User:
   │   │  │  email = guest@example.com
   │   │  │  first_name = John
   │   │  │  last_name = Doe
   │   │  │  phone = +234 800 000 0000
   │   │  │  password_hash = '' (empty)
   │   │  └─ Save user
   │   │
   │   ├─ Generate guest_code = "ABC123" (random 6 chars)
   │   │
   │   ├─ Create Booking:
   │   │  is_guest_booking = true
   │   │  guest_code = "ABC123"
   │   │  guest_email = "guest@example.com"
   │   │  guest_phone = "+234 800 000 0000"
   │   └─ Save to database
   │
   ├─→ Returns:
   │   {
   │     success: true,
   │     booking_id: 42,
   │     guest_code: "ABC123"
   │   }
   │
   └─→ Redirect to /bookings/42/confirmation
       └─→ Display guest code prominently
           └─→ "Save this code: ABC123"
               └─→ Guest bookmarks /bookings/guest/ABC123
```

### Admin Create Booking Flow

```
1. Admin visits /admin/create-booking
   │
   ├─→ Page loads with:
   │   - Guest type selector (registered/new)
   │   - Unit dropdown (fetched from /api/units)
   │   - Date inputs
   │   - Special requests textarea
   │
   ├─→ Admin selects:
   │   - Guest type: "New Guest"
   │   - Fills: email, phone, first name, last name
   │   - Unit: "Unit 001" (id=1)
   │   - Dates: 2024-01-15 to 2024-01-20
   │   - Requests: "VIP Guest"
   │   - Marks: "Paid" checkbox
   │
   ├─→ JavaScript:
   │   - Calls /api/units to get pricing
   │   - Updates price breakdown
   │   - Calculates total = 25000
   │
   ├─→ Admin clicks "Create Booking"
   │
   ├─→ POST /admin/create-booking with:
   │   {
   │     guest_email: "client@company.com",
   │     guest_phone: "+234 800 000 0000",
   │     guest_first_name: "Corporate",
   │     guest_last_name: "Client",
   │     unit_id: 1,
   │     check_in: "2024-01-15",
   │     check_out: "2024-01-20",
   │     num_guests: 4,
   │     mark_paid: true
   │   }
   │
   ├─→ Backend:
   │   ├─ Check if admin (@admin_required)
   │   ├─ Create or get Guest user
   │   ├─ Generate booking_reference = "ENI-XYZ98765"
   │   ├─ Generate guest_code = "XYZ789"
   │   ├─ Create Booking:
   │   │  status = 'confirmed' (because paid)
   │   │  paid = true
   │   │  is_guest_booking = true
   │   │  guest_code = "XYZ789"
   │   └─ Save
   │
   ├─→ Returns:
   │   {
   │     success: true,
   │     booking_id: 43,
   │     booking_reference: "ENI-XYZ98765",
   │     guest_code: "XYZ789"
   │   }
   │
   └─→ Admin sees: "Booking created! Reference: ENI-XYZ98765"
       └─→ Shares code with guest: "XYZ789"
           └─→ Guest visits /bookings/guest/XYZ789
               └─→ Can access booking without login
```

### Guest Code Access Flow

```
1. Guest receives email:
   "Your booking code: ABC123"
   "Visit: https://eni.com/bookings/guest/ABC123"
   │
   ├─→ Guest clicks link
   │
   ├─→ GET /bookings/guest/ABC123
   │
   ├─→ Backend:
   │   ├─ Query: SELECT * FROM bookings WHERE guest_code = "ABC123"
   │   ├─ Check:
   │   │  ├─ Booking exists? ✓
   │   │  ├─ Code matches? ✓
   │   │  ├─ Within dates?
   │   │  │   IF now() > check_out_date:
   │   │  │   └─ ERROR: "Code expired"
   │   │  │   ELSE:
   │   │  │   └─ ALLOW ACCESS ✓
   │   └─ Fetch full booking details
   │
   ├─→ Display booking details page:
   │   - Unit information
   │   - Check-in/out dates
   │   - Total price
   │   - Special requests
   │   - Services information
   │   - Contact support button
   │   - Request service button
   │
   └─→ Guest can:
       ├─ View all booking details
       ├─ Request services
       ├─ Get support contact info
       └─ Cannot modify booking (read-only)
```

## API Call Sequence Diagram

### Availability Check

```
Client                          Server
  │                               │
  ├──→ GET /api/availability      │
  │    ?unit_id=1                │
  │    &check_in=2024-01-15      │
  │    &check_out=2024-01-20     │
  │                               │
  │                          ┌────┴────┐
  │                          │ Query DB │
  │                          │ Bookings │
  │                          └────┬────┘
  │                               │
  │←── 200 OK                      │
  │    {                           │
  │      "is_available": true,     │
  │      "unit_number": "001",     │
  │      "base_price": 5000,       │
  │      "nights": 5,              │
  │      "total_price": 25000      │
  │    }                           │
  │                               │
  ├─ Update UI                    │
  │  Show success                 │
  │  Show price                   │
  │                               │
```

## Database Query Examples

### Check Availability
```sql
SELECT * FROM bookings 
WHERE unit_id = ? 
AND status != 'cancelled'
AND (
  (check_in_date <= ? AND check_out_date > ?)
  OR
  (check_in_date < ? AND check_out_date >= ?)
  OR
  (check_in_date >= ? AND check_out_date <= ?)
)
```

### Get Booking by Guest Code
```sql
SELECT * FROM bookings 
WHERE guest_code = ? 
AND guest_code IS NOT NULL
```

### Get User Bookings
```sql
SELECT * FROM bookings 
WHERE user_id = ? 
ORDER BY created_at DESC
```

### Get Admin Dashboard Stats
```sql
SELECT COUNT(*) FROM bookings  -- total_bookings
SELECT COUNT(*) FROM units     -- total_units
SELECT COUNT(*) FROM users     -- total_users
SELECT COUNT(*) FROM service_requests WHERE status = 'pending'
```

## Security Flow

### User Login
```
User enters email/password
  ↓
POST /auth/login with credentials
  ↓
Backend:
  ├─ Find user by email
  ├─ Check password with check_password()
  ├─ Create session
  └─ Set Flask-Login cookie
  ↓
Redirect to /guest/dashboard
```

### Admin Only Access
```
GET /admin/create-booking
  ↓
Backend checks:
  ├─ Is user authenticated? 
  │  └─ NO → Redirect to login
  ├─ Is user admin? (is_admin = true)
  │  └─ NO → Redirect to home + flash error
  └─ YES → Render form
```

## Performance Considerations

### Database Indexing
```sql
CREATE INDEX idx_guest_code ON bookings(guest_code);
CREATE INDEX idx_booking_reference ON bookings(booking_reference);
CREATE INDEX idx_user_email ON users(email);
CREATE INDEX idx_unit_number ON units(unit_number);
```

### Query Optimization
- ✅ Use foreign keys for relationship loads
- ✅ Index frequently searched columns
- ✅ Avoid N+1 queries (use joins)
- ✅ Cache unit pricing data

### Frontend Optimization
- ✅ Lazy load images
- ✅ Minify JavaScript
- ✅ Use CSS classes (no inline styles)
- ✅ Minimize API calls

## Caching Strategy

### Client-Side
- ✅ Cache unit list (valid for 1 hour)
- ✅ Cache services list (valid for 24 hours)
- ✅ Cache user session

### Server-Side (Future)
- ✅ Cache popular units
- ✅ Cache availability checks
- ✅ Cache dashboard stats

## Error Handling

### 400 Bad Request
```
Invalid dates
Missing required fields
Invalid unit ID
Availability conflicts
```

### 401 Unauthorized
```
Guest code not found
Not logged in
Session expired
```

### 403 Forbidden
```
Not admin
Cannot access other user's booking
```

### 404 Not Found
```
Unit not found
Booking not found
User not found
```

### 500 Server Error
```
Database connection error
Unexpected exception
```

## Deployment Architecture

```
┌─────────────────┐
│  Web Server     │
│  (Nginx/Apache) │
└────────┬────────┘
         ↓
┌─────────────────────┐
│  Flask Application  │
│  (Gunicorn/uWSGI)   │
└────────┬────────────┘
         ↓
┌─────────────────────┐
│  PostgreSQL DB      │
│  (Production)       │
└─────────────────────┘
```

## Summary

- **Modular**: Blueprints separate concerns
- **Scalable**: Can add more units, services, features easily
- **Secure**: Password hashing, session management, admin checks
- **Fast**: Indexed database, minimal queries
- **Responsive**: Works on all devices
- **User-Friendly**: Clear flows, instant feedback

---

For implementation details, see:
- `UPDATES.md` - Feature documentation
- `ROUTES.md` - API reference
- `models.py` - Database schema
