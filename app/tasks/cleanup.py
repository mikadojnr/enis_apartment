from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
from app import db
from app.models import Booking

def cleanup_expired_bookings():
    """Mark pending bookings as expired if past expires_at"""
    now = datetime.utcnow()
    expired = Booking.query.filter(
        Booking.status == 'pending',
        Booking.expires_at < now
    ).all()

    if expired:
        for booking in expired:
            booking.status = 'expired'
        db.session.commit()
        print(f"[Cleanup] Marked {len(expired)} bookings as expired at {now}")

def init_scheduler(app):
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        func=cleanup_expired_bookings,
        trigger="interval",
        minutes=5,                # check every 5 minutes
        id='expired_bookings_cleanup',
        name='Clean up expired pending bookings',
        replace_existing=True
    )
    scheduler.start()
    print("→ Expired bookings cleanup scheduler started (every 5 min)")