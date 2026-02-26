# Admin Quick Reference - Apartments & Gallery

## Admin URLs

| Feature | URL | Action |
|---------|-----|--------|
| Dashboard | `/admin/dashboard` | View dashboard |
| **Apartments** | `/admin/apartments` | List all apartment types |
| | `/admin/apartments/new` | Create new apartment |
| | `/admin/apartments/<id>/edit` | Edit apartment |
| | `/admin/apartments/<id>/delete` | Delete apartment |
| **Units** | `/admin/units` | List all units |
| | `/admin/units/new` | Create new unit |
| | `/admin/units/<id>/edit` | Edit unit |
| | `/admin/units/<id>/gallery` | Manage gallery |
| | `/admin/units/<id>/delete` | Delete unit |
| | `/admin/units/<id>/toggle` | Toggle availability |

## Step-by-Step Guides

### 1. Create a New Apartment Type

```
1. Go to /admin/apartments
2. Click "+ New Apartment Type" button
3. Fill in the form:
   - Name: "2-Bedroom Luxury"
   - Bedrooms: 2
   - Bathrooms: 2
   - Area: 120.5 (sqm)
   - Daily Price: 50000 (₦)
   - Description: Add detailed description
4. Click "Create Apartment Type"
5. You're now ready to add units of this type
```

### 2. Create a New Unit

```
1. Go to /admin/units
2. Click "+ New Unit" button
3. Fill in the form:
   - Unit Number: "A1"
   - Apartment Type: Select from dropdown
   - Floor: 3
   - View Type: "City View" (optional)
   - Featured Image: Paste URL of main image
4. Click "Create Unit"
5. You'll be redirected to gallery page
6. Add 3-5 images for the unit
```

### 3. Manage Gallery for a Unit

```
1. Go to /admin/units
2. Find your unit and click "Gallery" button
3. Click "+ Add Image"
4. In the modal:
   - Paste Image URL (must be externally hosted)
   - Add Label: "Living Room", "Master Bedroom", etc.
   - Add Description (optional): What's shown in the image
   - Check "Featured Image" for the unit listing thumbnail
5. Click "Save Image"
6. Repeat for each room/area
7. Gallery appears on /units/<id> for customers
```

### 4. Edit Unit Details

```
1. Go to /admin/units
2. Find unit and click "Edit" button
3. Modify:
   - Unit number
   - Apartment type
   - Floor
   - View type
   - Featured image URL
4. Click "Update Unit"
```

### 5. Edit Gallery Images

```
1. Go to /admin/units
2. Click "Gallery" for the unit
3. Find image and click "Edit"
4. Update:
   - Label (room name)
   - Description
   - Check/uncheck featured
5. Click "Save Image"
```

### 6. Delete Gallery Image

```
1. Go to /admin/units
2. Click "Gallery" for the unit
3. Find image and click "Delete"
4. Confirm deletion
```

### 7. Reorder Gallery Images

```
Currently: Manual ordering via display_order field
Future: Drag-and-drop interface coming

To reorder manually:
1. Edit each image
2. Set display_order (0, 1, 2, 3, etc.)
3. Lower numbers appear first
```

### 8. Mark Unit as Unavailable

```
1. Go to /admin/units
2. Find the unit
3. Click "Mark Unavailable" button
4. Unit no longer appears in searches
5. Click "Mark Available" to reactivate
```

## Image URL Examples

### Valid Image URLs
```
https://example.com/images/unit-a1.jpg
https://cdn.example.com/apartments/living-room.png
https://s3.amazonaws.com/bucket/image.jpg
https://cloudinary.example.com/image.jpg
```

### Not Valid
```
file:///home/user/images/photo.jpg  (local file)
../images/photo.jpg                  (relative path)
C:\Users\images\photo.jpg           (Windows path)
```

## Recommended Image Specifications

| Aspect | Specification |
|--------|---------------|
| Width | 1200px minimum |
| Height | 800px minimum |
| Format | JPG, PNG |
| Size | < 2MB per image |
| Aspect Ratio | 4:3 or 16:9 |
| Quality | High resolution |

## Label Naming Convention

**Recommended labels for consistent display:**
- Living Room
- Kitchen
- Master Bedroom
- Bedroom 2
- Bedroom 3
- Bathroom 1
- Bathroom 2
- Dining Area
- Hallway / Entrance
- Balcony / Patio
- Laundry Room
- Utility / Storage

## Common Tasks

### Task: Add photos of a renovated unit

```
1. /admin/units
2. Click Gallery on the unit
3. Delete old images one by one
4. Add new photos:
   - Get image URLs from cloud storage
   - Click "+ Add Image"
   - Paste URL
   - Add label
   - Save
5. Repeat for each new photo
6. Set best photo as featured
```

### Task: Create 5 new units quickly

```
1. Decide on apartment type
2. Have all images ready (hosted externally)
3. Go to /admin/units
4. For each unit:
   - Click "+ New Unit"
   - Fill form (unit number, floor, etc.)
   - Paste image URL
   - Create
   - Add gallery images from redirected page
5. All units now visible to customers
```

### Task: Update apartment pricing

```
1. Go to /admin/apartments
2. Find apartment and click "Edit"
3. Change daily price
4. Save
5. All units of this type automatically updated
```

### Task: Remove a unit

```
1. Go to /admin/units
2. Find unit and click "Edit"
3. Scroll to bottom
4. Click "Delete Unit"
5. Confirm
6. Note: Can't delete if unit has bookings
```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Image not displaying | Check URL is public, use HTTPS |
| Can't delete apartment | Delete all units first |
| Can't delete unit | Cancel bookings first |
| Gallery not showing | Add at least one image |
| Featured image not updating | Refresh page in browser |
| Image label too long | Keep under 120 characters |

## Tips & Tricks

1. **Before bulk upload** - Have all image URLs ready in a spreadsheet
2. **Use consistent labels** - Makes galleries look professional
3. **Featured image** - Choose your best/most appealing photo
4. **Description** - Add details about what makes the room special
5. **Mobile preview** - Test on phone to see how customers see it
6. **High quality images** - Professional photos boost bookings
7. **Keep order logical** - Living room → Kitchen → Bedrooms → Bathrooms

## Keyboard Shortcuts

While admin URLs not full SPA, useful shortcuts:
- `Tab` - Navigate form fields
- `Enter` - Submit form
- `Esc` - Close modals (when added)
- `Ctrl+S` - Submit form (browser default)

## Performance Notes

- Gallery images load in background (non-blocking)
- Thumbnails lazy-load on demand
- No API calls when switching images
- Works well on slow connections
- Mobile-optimized for 3G

## Security Notes

- All admin features require login
- Admin-only role required
- Input validation on all forms
- CSRF protection enabled
- SQL injection prevention via ORM
