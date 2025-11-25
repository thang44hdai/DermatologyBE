"""
Scheduler Service

Background job scheduler for medication reminders.
Checks reminders and sends Firebase notifications at scheduled times.
"""

import logging
import json
from datetime import datetime, timedelta, time as datetime_time
from typing import List, Optional
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config.settings import settings
from app.models.database import MedicationReminder, User
from app.services.notification_service import notification_service

logger = logging.getLogger(__name__)


class SchedulerService:
    """Service for scheduling medication reminder notifications"""
    
    def __init__(self):
        self.scheduler: Optional[AsyncIOScheduler] = None
        self.timezone = pytz.timezone(settings.NOTIFICATION_TIMEZONE)
        
        # Create database session for scheduler
        engine = create_engine(str(settings.DATABASE_URL))
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    def start(self):
        """Start the scheduler"""
        if self.scheduler and self.scheduler.running:
            logger.warning("Scheduler is already running")
            return
        
        self.scheduler = AsyncIOScheduler(timezone=self.timezone)
        
        # Check reminders every minute
        self.scheduler.add_job(
            self.check_and_send_reminders,
            CronTrigger(minute='*'),  # Every minute
            id='check_reminders',
            name='Check and send medication reminders',
            replace_existing=True
        )
        
        self.scheduler.start()
        logger.info("📅 Scheduler started - checking reminders every minute")
    
    def shutdown(self):
        """Shutdown the scheduler"""
        if self.scheduler and self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("🛑 Scheduler shutdown")
    
    async def check_and_send_reminders(self):
        """
        Check for reminders that should be sent now
        Called every minute by the scheduler
        """
        db = self.SessionLocal()
        try:
            now = datetime.now(self.timezone)
            current_time = now.time()
            current_date = now.date()
            current_day_of_week = now.weekday()  # 0=Monday, 6=Sunday
            
            logger.debug(f"Checking reminders at {now.strftime('%Y-%m-%d %H:%M')}")
            
            # Get all active reminders
            reminders = db.query(MedicationReminder).filter(
                MedicationReminder.is_active == True,
                MedicationReminder.start_date <= current_date
            ).all()
            
            for reminder in reminders:
                # Check if reminder has ended
                if reminder.end_date and reminder.end_date < current_date:
                    continue
                
                # Check if reminder should trigger today
                should_trigger = False
                
                if reminder.frequency == 'daily':
                    should_trigger = True
                
                elif reminder.frequency == 'weekly':
                    # Check if today is in the selected days
                    if reminder.days_of_week:
                        try:
                            days = json.loads(reminder.days_of_week)
                            should_trigger = current_day_of_week in days
                        except:
                            logger.error(f"Invalid days_of_week for reminder {reminder.id}")
                
                elif reminder.frequency == 'custom':
                    should_trigger = True
                
                if not should_trigger:
                    continue
                
                # Check if current time matches any reminder time
                try:
                    times = json.loads(reminder.times)
                    
                    for time_str in times:
                        # Parse time (HH:MM)
                        hour, minute = map(int, time_str.split(':'))
                        reminder_time = datetime_time(hour, minute)
                        
                        # Check if current time matches (within the same minute)
                        if current_time.hour == reminder_time.hour and current_time.minute == reminder_time.minute:
                            # Send notification
                            await self.send_reminder_notification(db, reminder, now)
                
                except Exception as e:
                    logger.error(f"Error checking reminder {reminder.id}: {e}")
            
        except Exception as e:
            logger.error(f"Error in check_and_send_reminders: {e}")
        finally:
            db.close()
    
    async def send_reminder_notification(
        self,
        db: Session,
        reminder: MedicationReminder,
        scheduled_time: datetime
    ):
        """
        Send push notification for a reminder
        
        Args:
            db: Database session
            reminder: MedicationReminder object
            scheduled_time: When the reminder is scheduled
        """
        try:
            # Get user
            user = db.query(User).filter(User.id == reminder.user_id).first()
            if not user:
                logger.error(f"User {reminder.user_id} not found for reminder {reminder.id}")
                return
            
            # Prepare notification data
            title = "💊 Nhắc nhở uống thuốc"
            body = f"{reminder.title} - {reminder.medicine_name}"
            if reminder.dosage:
                body += f" ({reminder.dosage})"
            
            # Send Firebase notification
            success = await notification_service.send_reminder_notification(
                user_id=user.id,
                reminder_id=reminder.id,
                title=title,
                body=body,
                scheduled_time=scheduled_time
            )
            
            if success:
                logger.info(f"✅ Sent reminder notification for {reminder.medicine_name} to user {user.id}")
            else:
                logger.warning(f"⚠️ Failed to send reminder notification to user {user.id}")
        
        except Exception as e:
            logger.error(f"Error sending reminder notification: {e}")


# Create singleton instance
scheduler_service = SchedulerService()
