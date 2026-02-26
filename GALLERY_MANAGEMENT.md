# Gallery & Apartment Management System

## Overview

The system includes a comprehensive gallery management system for apartment units, allowing admins to:
- Create and manage apartment types
- Create and manage individual units
- Upload and organize gallery images with labels
- Display galleries to customers during browsing

## Database Schema

### New Models

#### UnitImage Model
Stores gallery images for each apartment unit with metadata:

```python
class UnitImage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    unit_id = db.Column(db.Integer, db.ForeignKey('units.id'), nullable=False)
    image_url = db.Column(db.String(255), nullable=False)
    label = db.Column(db.String(120))  # e.g., "Living Room", "Master Bedroom"
    description = db.Column(db.Text)
    display_order = db.Column(db.Integer, default=0)
    is_featured = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
```

### Updated Unit Model
Added relationship to gallery images:
```python
gallery_images = db.relationship('UnitImage', backref='unit', lazy='dynamic', cascade='all, delete-orphan')
```

## Admin Features

### 1. Apartment Type Management

**URL**: `/admin/apartments`

#### Features:
- View all apartment types
- Create new apartment types with:
  - Name (e.g., "2-Bedroom Luxury")
  - Bedrooms and bathrooms count
  - Square footage (sqm)
  - Base daily price
  - Detailed description
- Edit apartment type details
- Delete apartment types (only if no units exist)
- View active units per apartment type

#### Create New Apartment:
```
POST /admin/apartments/new
{
  "name": "2-Bedroom Luxury",
  "bedrooms": 2,
  "bathrooms": 2,
  "area_sqm": 120.5,
  "description": "...",
  "base_price": 50000
}
```

#### Edit Apartment:
```
POST /admin/apartments/<apartment_id>/edit
{
  "name": "...",
  "bedrooms": 2,
  ...
}
```

#### Delete Apartment:
```
POST /admin/apartments/<apartment_id>/delete
```

### 2. Unit Management

**URL**: `/admin/units`

#### Features:
- View all units with current status
- Create new units with:
  - Unit number (e.g., "A1", "B2")
  - Apartment type selection
  - Floor number
  - View type (e.g., "City View", "Garden View")
  - Featured image URL
- Edit unit details
- Delete units (only if no bookings exist)
- Toggle availability status
- Access gallery management for each unit

#### Create New Unit:
```
POST /admin/units/new
{
  "unit_number": "Unit A1",
  "apartment_type_id": 1,
  "floor": 3,
  "view": "City View",
  "image_url": "https://example.com/image.jpg"
}
```

#### Edit Unit:
```
POST /admin/units/<unit_id>/edit
{
  "unit_number": "Unit A1",
  ...
}
```

#### Toggle Availability:
```
POST /admin/units/<unit_id>/toggle
```

### 3. Gallery Management

**URL**: `/admin/units/<unit_id>/gallery`

#### Features:
- View all images for a unit
- Add new gallery images with:
  - Image URL (external link)
  - Label (e.g., "Living Room", "Master Bedroom", "Kitchen")
  - Description of the image
  - Mark as featured (shown on unit listings)
  - Display order for custom sorting
- Edit image metadata
- Delete images
- Reorder images (drag & drop capable)
- Image preview before saving

#### Add Gallery Image:
```
POST /admin/units/<unit_id>/gallery/add
{
  "image_url": "https://example.com/image.jpg",
  "label": "Living Room",
  "description": "Spacious living area with city views",
  "is_featured": true
}
```

#### Edit Gallery Image:
```
POST /admin/gallery/<image_id>/edit
{
  "label": "Updated Label",
  "description": "Updated description",
  "is_featured": false,
  "display_order": 2
}
```

#### Delete Gallery Image:
```
POST /admin/gallery/<image_id>/delete
```

#### Reorder Images:
```
POST /admin/units/<unit_id>/gallery/reorder
{
  "image_order": [3, 1, 2, 4]  // Array of image IDs in desired order
}
```

## Customer/Guest Features

### Gallery Display on Unit Details Page

When customers view a unit at `/units/<unit_id>`, they see:

1. **Main Featured Image**
   - If no featured image, shows the unit's default image
   - If no default image, shows first gallery image
   - Displays label in top-right corner

2. **Gallery Thumbnails**
   - Grid of all gallery images below main image
   - Click any thumbnail to change main image
   - Featured images marked with green dot
   - Hover effects for better UX

3. **Image Information**
   - Each image displays its label
   - Descriptions appear in hover (desktop) or below (mobile)
   - Images in logical order (Living Room, Bedrooms, Kitchen, etc.)

### Gallery Image Features

- **Responsive Design**
  - Main image: 400px height on desktop, 200px on mobile
  - Thumbnails: 6 per row on desktop, 3 on tablet, 2 on mobile
  - Smooth transitions and hover effects

- **Accessibility**
  - All images have alt text
  - Keyboard navigation support
  - Screen reader friendly

- **Performance**
  - Lazy loading for gallery thumbnails
  - Optimized image sizes
  - No database queries on image switching (client-side only)

## Workflow Examples

### Example 1: Creating a New Apartment Type and Units

1. Admin navigates to `/admin/apartments`
2. Click "+ New Apartment Type"
3. Fill in details:
   - Name: "3-Bedroom Executive"
   - Bedrooms: 3, Bathrooms: 2.5
   - Area: 180 sqm
   - Price: 75,000 per day
4. Save and returns to apartments list
5. Admin navigates to `/admin/units`
6. Click "+ New Unit"
7. Select the new apartment type
8. Fill in: Unit A3, Floor 5, City View
9. Save - redirects to gallery page
10. Click "+ Add Image" multiple times:
    - Living Room (featured)
    - Master Bedroom
    - Guest Bedroom
    - Kitchen
    - Bathrooms
11. Customers can now see full gallery when browsing

### Example 2: Updating Unit Gallery

1. Admin at `/admin/units`
2. Find "Unit A3" and click "Gallery"
3. See all current images
4. Edit "Master Bedroom" image:
   - Update description with new details
   - Click Save
5. Delete poor quality images
6. Add new images for recently renovated areas
7. Reorder images to logical flow
8. Changes immediately visible to customers

## Image URL Guidelines

Images must be stored externally and accessed via URL. Recommended approaches:

1. **Cloud Storage** (Recommended)
   - AWS S3
   - Google Cloud Storage
   - Azure Blob Storage
   - Cloudinary
   - Imgur

2. **Server Storage**
   - Direct URLs to images on your server
   - Example: `https://yourdomain.com/images/unit-a1-living-room.jpg`

## Best Practices

### Image Organization
- Use descriptive labels (room type, angle, features)
- Include descriptions for accessibility
- Keep 3-5 images per unit minimum
- Maximum 15-20 images per unit recommended

### Image Quality
- Use high-resolution images (min 1200px width)
- Consistent lighting and styling
- Professional photography recommended
- Images should clearly show room layout and furnishings

### Labeling Convention
- "Living Room"
- "Master Bedroom" / "Bedroom 2" / "Bedroom 3"
- "Kitchen"
- "Bathroom 1" / "Bathroom 2"
- "Dining Area"
- "Entrance/Hallway"
- "Balcony/Patio"
- "Laundry/Utility"

### Featured Image
- Set ONE image as featured (appears on unit listing)
- Choose the most appealing room or overview shot
- Typically the living room or best angle of the unit

## API Endpoints Summary

```
// Apartments
GET    /admin/apartments              - List all apartment types
GET    /admin/apartments/new          - Create apartment form
POST   /admin/apartments/new          - Create apartment
GET    /admin/apartments/<id>/edit    - Edit apartment form
POST   /admin/apartments/<id>/edit    - Save apartment changes
POST   /admin/apartments/<id>/delete  - Delete apartment

// Units
GET    /admin/units                   - List all units
GET    /admin/units/new               - Create unit form
POST   /admin/units/new               - Create unit
GET    /admin/units/<id>/edit         - Edit unit form
POST   /admin/units/<id>/edit         - Save unit changes
POST   /admin/units/<id>/delete       - Delete unit
POST   /admin/units/<id>/toggle       - Toggle availability

// Gallery
GET    /admin/units/<unit_id>/gallery           - View gallery
POST   /admin/units/<unit_id>/gallery/add       - Add image
POST   /admin/gallery/<image_id>/edit           - Edit image
POST   /admin/gallery/<image_id>/delete         - Delete image
POST   /admin/units/<unit_id>/gallery/reorder   - Reorder images
```

## Troubleshooting

### Images Not Displaying
- Check image URL is publicly accessible
- Verify URL protocol (http vs https)
- Test URL in browser directly
- Check file size (use compressed images)

### Gallery Not Showing
- Ensure at least one image is added
- Check image URLs are valid
- Clear browser cache
- Reload page

### Display Order Not Updating
- Reorder feature updates client-side - refresh to confirm
- All images must have valid display_order values
- Use reorder endpoint to batch update

## Future Enhancements

Possible improvements:
- Bulk image upload from ZIP file
- Image cropping and editing tools
- Automatic image optimization
- 360° virtual tours
- Video support
- Before/after image comparisons
- Image analytics (popular images)
