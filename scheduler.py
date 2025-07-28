from apscheduler.schedulers.background import BackgroundScheduler
from utils.notifications import NotificationManager
import logging
import atexit

def init_scheduler(app):
    """Initialize the background scheduler for notifications"""
    scheduler = BackgroundScheduler()
    
    def scheduled_notification_check():
        """Scheduled function to check notifications"""
        with app.app_context():
            notification_manager = NotificationManager()
            notification_manager.run_daily_checks()
    
    # Schedule daily check at 8:00 AM
    scheduler.add_job(
        func=scheduled_notification_check,
        trigger="cron",
        hour=8,
        minute=0,
        id='daily_notification_check'
    )
    
    # Start the scheduler
    scheduler.start()
    logging.info("Background scheduler started - daily notifications at 8:00 AM")
    
    # Shut down the scheduler when exiting the app
    atexit.register(lambda: scheduler.shutdown())
