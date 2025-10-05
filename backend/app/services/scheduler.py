"""
Background scheduler for periodic alert checking
"""
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from backend.app.database import SessionLocal
from backend.app.services.alert_service import AlertService
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Global scheduler instance
scheduler = None


def check_alerts_job():
    """Job function to check all alerts"""
    logger.info(f"Starting alert check job at {datetime.utcnow().isoformat()}")
    
    db = SessionLocal()
    try:
        alert_service = AlertService(db)
        result = alert_service.check_all_active_alerts()
        
        logger.info(
            f"Alert check completed: {result['checked_count']} checked, "
            f"{result['triggered_count']} triggered, {result['error_count']} errors"
        )
        
        # Log triggered alerts
        if result['triggered_alerts']:
            for alert in result['triggered_alerts']:
                logger.info(
                    f"Alert triggered: {alert['stock_name']} ({alert['ticker_symbol']}) - "
                    f"{alert['alert_type']} {alert['condition']} {alert['threshold_value']}"
                )
    except Exception as e:
        logger.error(f"Error in alert check job: {str(e)}")
    finally:
        db.close()


def start_scheduler(interval_minutes: int = 15):
    """
    Start the background scheduler for alert checking
    
    Args:
        interval_minutes: How often to check alerts (default: 15 minutes)
    """
    global scheduler
    
    if scheduler is not None:
        logger.warning("Scheduler already running")
        return
    
    scheduler = BackgroundScheduler()
    
    # Add job to check alerts every X minutes
    scheduler.add_job(
        func=check_alerts_job,
        trigger=IntervalTrigger(minutes=interval_minutes),
        id='check_alerts_job',
        name='Check all active alerts',
        replace_existing=True
    )
    
    scheduler.start()
    logger.info(f"Alert scheduler started - checking every {interval_minutes} minutes")


def stop_scheduler():
    """Stop the background scheduler"""
    global scheduler
    
    if scheduler is not None:
        scheduler.shutdown()
        scheduler = None
        logger.info("Alert scheduler stopped")


def get_scheduler_status():
    """Get the current status of the scheduler"""
    global scheduler
    
    if scheduler is None:
        return {
            'running': False,
            'jobs': []
        }
    
    jobs = []
    for job in scheduler.get_jobs():
        jobs.append({
            'id': job.id,
            'name': job.name,
            'next_run_time': job.next_run_time.isoformat() if job.next_run_time else None
        })
    
    return {
        'running': True,
        'jobs': jobs
    }
