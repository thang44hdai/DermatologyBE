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
from app.models import MedicationReminder, User
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
                if reminder.end_date and reminder.end_date.date() < current_date:
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
                    times_data = json.loads(reminder.times)
                    
                    # Xử lý tương thích ngược
                    if times_data and isinstance(times_data[0], str):
                        # Format cũ: ["07:00", "12:00", "18:00"]
                        time_strings = times_data
                        dosage_map = {}  # Không có thông tin dosage
                    else:
                        # Format mới: [{"time": "07:00", "period": "morning", "dosage": "2"}, ...]
                        time_strings = [t['time'] for t in times_data]
                        # Tạo map giờ -> dosage để pass vào notification
                        dosage_map = {t['time']: t.get('dosage', '1') for t in times_data}
                    
                    for time_str in time_strings:
                        # Parse time (HH:MM)
                        hour, minute = map(int, time_str.split(':'))
                        reminder_time = datetime_time(hour, minute)
                        
                        # Check if current time matches (within the same minute)
                        if current_time.hour == reminder_time.hour and current_time.minute == reminder_time.minute:
                            # Get dosage for this time
                            dosage_for_time = dosage_map.get(time_str, reminder.dosage)
                            
                            # Send notification with dosage info
                            await self.send_reminder_notification(db, reminder, now, dosage_for_time)
                
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
        scheduled_time: datetime,
        dosage: str = None
    ):
        """
        Send push notification for a reminder
        
        Args:
            db: Database session
            reminder: MedicationReminder object
            scheduled_time: When the reminder is scheduled
            dosage: Dosage for this specific time (from new format)
        """
        try:
            # Get user
            user = db.query(User).filter(User.id == reminder.user_id).first()
            if not user:
                logger.error(f"User {reminder.user_id} not found for reminder {reminder.id}")
                return
            
            # Check if notification is enabled for this reminder
            if not reminder.is_notification_enabled:
                logger.info(f"⏸️ Skipped notification for reminder {reminder.id} (disabled by user)")
                return
            
            # Prepare notification message
            title = "💊 Nhắc Nhở Uống Thuốc"
            
            # Build body with dosage info
            body = f"Đến giờ uống {reminder.medicine_name}!"
            
            # Add dosage info (prioritize per-time dosage from new format)
            if dosage and reminder.unit:
                body += f" - Liều lượng: {dosage} {reminder.unit}"
            elif dosage:
                body += f" - Liều lượng: {dosage}"
            elif reminder.dosage and reminder.unit:
                body += f" - Liều lượng: {reminder.dosage} {reminder.unit}"
            
            # Add meal timing if available
            if reminder.meal_timing:
                body += f" ({reminder.meal_timing})"
            
            # Add notes if available
            if reminder.notes:
                body += f"\n💡 {reminder.notes}"
            
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
