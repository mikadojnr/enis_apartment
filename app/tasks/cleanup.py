from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
from app import db
from app.models import Booking

def cleanup_expired_bookings(app):
    """Mark pending bookings as expired if past expires_at"""
    from datetime import datetime

    with app.app_context():
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

def complete_finished_bookings(app):
    """Mark paid bookings as completed after checkout time has passed"""
    from datetime import datetime

    with app.app_context():
        now = datetime.utcnow()

        completed = Booking.query.filter(
            Booking.paid == True,
            Booking.status.in_(['confirmed', 'in_progress']),  # adjust based on your flow
            Booking.check_out_date < now
        ).all()

        if completed:
            for booking in completed:
                booking.status = 'completed'

            db.session.commit()

            print(f"[Cleanup] Marked {len(completed)} bookings as completed at {now}")

def init_scheduler(app):
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        func=cleanup_expired_bookings,
        args=[app],
        trigger="interval",
        minutes=5,                # check every 5 minutes
        id='expired_bookings_cleanup',
        name='Clean up expired pending bookings',
        replace_existing=True
    )

    # ✅ NEW: Completed bookings
    scheduler.add_job(
        func=complete_finished_bookings,
        args=[app],
        trigger="interval",
        minutes=10,   # every 10 min is fine (no need for high frequency)
        id='completed_bookings_update',
        replace_existing=True
    )
    scheduler.start()
    print("→ Expired bookings cleanup scheduler started (every 5 min)")