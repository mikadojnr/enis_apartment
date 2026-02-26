# Eni's Apartments - Complete Route Reference

## Public Routes (No Authentication Required)

### Main Pages
| Route | Method | File | Purpose |
|-------|--------|------|---------|
| `/` | GET | `main/routes.py` | Landing page |
| `/units` | GET | `main/routes.py` | Browse all units |
| `/units/<id>` | GET | `main/routes.py` | Unit details page |
| `/services` | GET | `main/routes.py` | Services page |
| `/about` | GET | `main/routes.py` | About page |
| `/contact` | GET | `main/routes.py` | Contact page |

### Authentication Routes
| Route | Method | File | Purpose |
|-------|--------|------|---------|
| `/auth/login` | GET, POST | `auth/routes.py` | User login page |
| `/auth/register` | GET, POST | `auth/routes.py` | User registration |
| `/auth/logout` | GET | `auth/routes.py` | User logout |

### Booking Routes (Partially Public)
| Route | Method | File | Purpose |
|-------|--------|------|---------|
| `/bookings/availability` | GET | `bookings/routes.py` | Search available units |
| `/bookings/new` | GET, POST | `bookings/routes.py` | Create new booking |
| `/bookings/<id>/confirmation` | GET | `bookings/routes.py` | View booking confirmation |
| `/bookings/guest/<guest_code>` | GET | `bookings/routes.py` | Guest code access |

## Authenticated User Routes

### Profile Management
| Route | Method | File | Purpose |
|-------|--------|------|---------|
| `/auth/profile` | GET, POST | `auth/routes.py` | View/edit profile |
| `/auth/change-password` | POST | `auth/routes.py` | Change password |

### Booking Management
| Route | Method | File | Purpose |
|-------|--------|------|---------|
| `/bookings/dashboard` | GET | `bookings/routes.py` | View guest dashboard |
| `/bookings/<id>` | GET | `bookings/routes.py` | View booking details |
| `/bookings/<id>/cancel` | POST | `bookings/routes.py` | Cancel booking |

### Service Management
| Route | Method | File | Purpose |
|-------|--------|------|---------|
| `/services/request` | GET, POST | `services/routes.py` | Create service request |
| `/services/my-requests` | GET | `services/routes.py` | View service requests |

## Admin Routes (Admin Only)

### Dashboard & Overview
| Route | Method | File | Purpose |
|-------|--------|------|---------|
| `/admin/dashboard` | GET | `admin/routes.py` | Admin overview |

### Unit Management
| Route | Method | File | Purpose |
|-------|--------|------|---------|
| `/admin/units` | GET | `admin/routes.py` | Manage units |
| `/admin/units/<id>/toggle` | POST | `admin/routes.py` | Toggle unit availability |

### Booking Management
| Route | Method | File | Purpose |
|-------|--------|------|---------|
| `/admin/bookings` | GET | `admin/routes.py` | View all bookings |
| `/admin/bookings/<id>/status` | POST | `admin/routes.py` | Update booking status |
| `/admin/create-booking` | GET, POST | `admin/routes.py` | Create booking for guest |

### Service Management
| Route | Method | File | Purpose |
|-------|--------|------|---------|
| `/admin/service-requests` | GET | `admin/routes.py` | View service requests |
| `/admin/service-requests/<id>/status` | POST | `admin/routes.py` | Update service status |

## API Endpoints

### Units API
| Route | Method | File | Purpose |
|-------|--------|------|---------|
| `/api/units` | GET | `api/routes.py` | Get all units (JSON) |
| `/api/units/<id>` | GET | `api/routes.py` | Get unit details (JSON) |
| `/api/availability` | GET | `api/routes.py` | Check unit availability |

### Bookings API
| Route | Method | File | Purpose |
|-------|--------|------|---------|
| `/api/bookings` | GET | `api/routes.py` | Get user bookings (JSON) |
| `/api/user/bookings` | GET | `api/routes.py` | Get current user bookings |

### Services API
| Route | Method | File | Purpose |
|-------|--------|------|---------|
| `/api/services` | GET | `api/routes.py` | Get all services (JSON) |

## Query Parameters

### Availability Check
```
/bookings/availability?check_in=2024-01-15&check_out=2024-01-20&type=1
```
- `check_in` - Date in YYYY-MM-DD format
- `check_out` - Date in YYYY-MM-DD format
- `type` - Apartment type ID (optional)

### Admin Bookings Filter
```
/admin/bookings?status=pending
```
- `status` - Filter by status: `all`, `pending`, `confirmed`, `completed`, `cancelled`

### Service Requests Filter
```
/admin/service-requests?status=pending
```
- `status` - Filter by status: `pending`, `in_progress`, `completed`

## Request/Response Examples

### Create Booking (POST /bookings/new)
**Request:**
```json
{
  "unit_id": 1,
  "check_in": "2024-01-15T00:00:00",
  "check_out": "2024-01-20T00:00:00",
  "num_guests": 2,
  "special_requests": "Early check-in if possible",
  "guest_email": "guest@example.com",
  "guest_phone": "+234 800 000 0000",
  "guest_first_name": "John",
  "guest_last_name": "Doe"
}
```

**Response:**
```json
{
  "success": true,
  "booking_id": 42,
  "guest_code": "ABC123"
}
```

### Check Availability (GET /api/availability)
**Request:**
```
/api/availability?unit_id=1&check_in=2024-01-15&check_out=2024-01-20
```

**Response:**
```json
{
  "unit_id": 1,
  "unit_number": "Unit 001",
  "is_available": true,
  "base_price": 5000,
  "nights": 5,
  "total_price": 25000
}
```

### Get Unit (GET /api/units/1)
**Response:**
```json
{
  "id": 1,
  "unit_number": "Unit 001",
  "floor": 1,
  "view": "City View",
  "is_available": true,
  "apartment_type": {
    "id": 1,
    "name": "2 Bedroom",
    "bedrooms": 2,
    "bathrooms": 2,
    "area_sqm": 95,
    "base_price": 5000
  }
}
```

### Update Booking Status (POST /admin/bookings/<id>/status)
**Request:**
```json
{
  "status": "confirmed"
}
```

**Response:**
```json
{
  "success": true,
  "status": "confirmed"
}
```

### Update Profile (POST /auth/profile)
**Request:**
```json
{
  "first_name": "John",
  "last_name": "Doe",
  "phone": "+234 800 000 0000"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Profile updated successfully"
}
```

### Change Password (POST /auth/change-password)
**Request:**
```json
{
  "current_password": "oldpassword",
  "new_password": "newpassword123"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Password changed successfully"
}
```

### Create Admin Booking (POST /admin/create-booking)
**Request:**
```json
{
  "user_id": 5,
  "unit_id": 1,
  "check_in": "2024-01-15",
  "check_out": "2024-01-20",
  "num_guests": 2,
  "special_requests": "VIP guest",
  "mark_paid": true,
  "is_admin_booking": true
}
```

**Response:**
```json
{
  "success": true,
  "booking_id": 42,
  "booking_reference": "ENI-ABC12345",
  "guest_code": "XYZ789"
}
```

## Status Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 201 | Created |
| 400 | Bad Request |
| 401 | Unauthorized |
| 403 | Forbidden (insufficient permissions) |
| 404 | Not Found |
| 500 | Server Error |

## Authentication Headers

Include for authenticated requests:
```
Authorization: Bearer <token>
```
(For Session-based auth, cookies are automatically included)

## Error Responses

### Authentication Error
```json
{
  "success": false,
  "message": "Unauthorized - please log in",
  "status": 401
}
```

### Validation Error
```json
{
  "success": false,
  "message": "Invalid check-out date",
  "status": 400
}
```

### Not Found
```json
{
  "success": false,
  "message": "Booking not found",
  "status": 404
}
```

## Navigation Flow

### New User Journey
```
/ → /units → /units/<id> → Check dates on page
  ↓ Available
  /bookings/new (fill form) → /bookings/<id>/confirmation
  ↓ Guest Code Access
  /bookings/guest/<code> → View booking
```

### Registered User Journey
```
/ → /auth/login → /guest/dashboard
  → /auth/profile (manage account)
  → /bookings/availability (search) 
  → /bookings/new → /bookings/<id>/confirmation
```

### Admin Journey
```
/admin/dashboard → Choose action:
  - /admin/units (manage)
  - /admin/bookings (view/update)
  - /admin/create-booking (new booking for guest)
  - /admin/service-requests (manage requests)
```

## Common Use Cases

### Registering a New Account
```
1. GET /auth/register
2. Fill form and submit
3. POST /auth/register
4. Redirect to /auth/login
5. Login and redirect to /guest/dashboard
```

### Booking a Unit
```
1. GET /units (browse units)
2. GET /units/<id> (view unit)
3. Fill dates and check availability (inline)
4. POST /bookings/new with booking data
5. GET /bookings/<id>/confirmation (view confirmation)
```

### Admin Creating Booking
```
1. GET /admin/dashboard
2. Click "New Booking"
3. GET /admin/create-booking
4. Fill form and select unit
5. POST /admin/create-booking
6. Receive booking reference and guest code
```

### Guest Accessing via Code
```
1. Receive email with guest code (e.g., "ABC123")
2. Visit /bookings/guest/ABC123
3. View booking details
4. Request services or contact support
```
