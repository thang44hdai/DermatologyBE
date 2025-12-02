"""
Medication Reminder Service

Business logic for managing medication reminders.
"""

import json
import logging
from datetime import datetime, date
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from fastapi import HTTPException, status

from app.models.database import MedicationReminder, Medicines
from app.schemas.reminder import ReminderCreate, ReminderUpdate

logger = logging.getLogger(__name__)


class ReminderService:
    """Service class for medication reminder operations"""
    
    @staticmethod
    def create_reminder(
        db: Session,
        reminder_data: ReminderCreate,
        user_id: int
    ) -> MedicationReminder:
        """
        Create a new medication reminder
        
        Args:
            db: Database session
            reminder_data: Reminder creation data
            user_id: ID of the user creating the reminder
            
        Returns:
            Created MedicationReminder object
            
        Raises:
            HTTPException: If medicine_id is invalid or validation fails
        """
        # Validate medicine_id if provided
        if reminder_data.medicine_id:
            medicine = db.query(Medicines).filter(
                Medicines.id == reminder_data.medicine_id
            ).first()
            if not medicine:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Medicine with ID {reminder_data.medicine_id} not found"
                )
        
        # Validate dates
        if reminder_data.end_date and reminder_data.end_date < reminder_data.start_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="End date cannot be before start date"
            )
        
        # Validate frequency-specific fields
        if reminder_data.frequency in ['weekly', 'specific_days'] and not reminder_data.days_of_week:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="days_of_week required for weekly or specific_days frequency"
            )
        
        # Auto-convert weekly with all 7 days to daily
        frequency = reminder_data.frequency
        days_of_week = reminder_data.days_of_week
        
        if frequency in ["weekly", "specific_days"] and days_of_week and len(days_of_week) == 7:
            frequency = "daily"
            days_of_week = None
            logger.info(f"Auto-converted weekly/specific_days (all 7 days) to daily for user {user_id}")
        
        # Serialize times as TimeSchedule objects
        times_json = json.dumps([t.model_dump() for t in reminder_data.times])
        
        # Create reminder
        reminder = MedicationReminder(
            user_id=user_id,
            medicine_id=reminder_data.medicine_id,
            medicine_name=reminder_data.medicine_name,
            dosage=reminder_data.dosage,
            unit=reminder_data.unit,
            meal_timing=reminder_data.meal_timing,
            frequency=frequency,
            times=times_json,
            days_of_week=json.dumps(days_of_week) if days_of_week else None,
            start_date=reminder_data.start_date,
            end_date=reminder_data.end_date,
            is_notification_enabled=reminder_data.is_notification_enabled,
            notes=reminder_data.notes,
            is_active=True
        )
        
        db.add(reminder)
        db.commit()
        db.refresh(reminder)
        
        logger.info(f"Created reminder {reminder.id} for user {user_id}: {reminder.title}")
        return reminder
    
    @staticmethod
    def get_reminders(
        db: Session,
        user_id: int,
        skip: int = 0,
        limit: int = 50,
        is_active: Optional[bool] = None,
        frequency: Optional[str] = None
    ) -> Tuple[List[MedicationReminder], int]:
        """
        Get user's medication reminders with filters
        
        Args:
            db: Database session
            user_id: User ID
            skip: Number of records to skip
            limit: Maximum number of records
            is_active: Filter by active status
            frequency: Filter by frequency type
            
        Returns:
            Tuple of (reminders list, total count)
        """
        query = db.query(MedicationReminder).filter(
            MedicationReminder.user_id == user_id
        )
        
        # Apply filters
        if is_active is not None:
            query = query.filter(MedicationReminder.is_active == is_active)
        
        if frequency:
            query = query.filter(MedicationReminder.frequency == frequency)
        
        # Get total count
        total = query.count()
        
        # Apply pagination and ordering
        reminders = query.order_by(
            MedicationReminder.created_at.desc()
        ).offset(skip).limit(limit).all()
        
        return reminders, total
    
    @staticmethod
    def get_reminder(
        db: Session,
        reminder_id: int,
        user_id: int
    ) -> MedicationReminder:
        """
        Get a specific reminder by ID
        
        Args:
            db: Database session
            reminder_id: Reminder ID
            user_id: User ID (for authorization)
            
        Returns:
            MedicationReminder object
            
        Raises:
            HTTPException: If reminder not found or doesn't belong to user
        """
        reminder = db.query(MedicationReminder).filter(
            MedicationReminder.id == reminder_id
        ).first()
        
        if not reminder:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Reminder not found"
            )
        
        # Verify ownership
        if reminder.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this reminder"
            )
        
        return reminder
    
    @staticmethod
    def update_reminder(
        db: Session,
        reminder_id: int,
        user_id: int,
        update_data: ReminderUpdate
    ) -> MedicationReminder:
        """
        Update a medication reminder
        
        Args:
            db: Database session
            reminder_id: Reminder ID to update
            user_id: User ID (for authorization)
            update_data: Update data
            
        Returns:
            Updated MedicationReminder object
            
        Raises:
            HTTPException: If reminder not found or validation fails
        """
        # Get existing reminder
        reminder = ReminderService.get_reminder(db, reminder_id, user_id)
        
        # Update fields
        update_dict = update_data.model_dump(exclude_unset=True)
        
        for field, value in update_dict.items():
            if field == 'times' and value is not None:
                # Serialize TimeSchedule objects
                setattr(reminder, field, json.dumps([t.model_dump() for t in value]))
            elif field == 'days_of_week' and value is not None:
                setattr(reminder, field, json.dumps(value))
            else:
                setattr(reminder, field, value)
        
        db.commit()
        db.refresh(reminder)
        
        logger.info(f"Updated reminder {reminder_id} for user {user_id}")
        return reminder
    
    @staticmethod
    def delete_reminder(
        db: Session,
        reminder_id: int,
        user_id: int
    ) -> None:
        """
        Delete a medication reminder
        
        Args:
            db: Database session
            reminder_id: Reminder ID to delete
            user_id: User ID (for authorization)
            
        Raises:
            HTTPException: If reminder not found
        """
        reminder = ReminderService.get_reminder(db, reminder_id, user_id)
        
        db.delete(reminder)
        db.commit()
        
        logger.info(f"Deleted reminder {reminder_id} for user {user_id}")
    
    @staticmethod
    def toggle_reminder(
        db: Session,
        reminder_id: int,
        user_id: int
    ) -> MedicationReminder:
        """
        Toggle reminder active status
        
        Args:
            db: Database session
            reminder_id: Reminder ID
            user_id: User ID (for authorization)
            
        Returns:
            Updated MedicationReminder object
        """
        reminder = ReminderService.get_reminder(db, reminder_id, user_id)
        
        reminder.is_active = not reminder.is_active
        db.commit()
        db.refresh(reminder)
        
        status_str = "activated" if reminder.is_active else "deactivated"
        logger.info(f"{status_str} reminder {reminder_id} for user {user_id}")
        
        return reminder
    
    @staticmethod
    def get_calendar_overview(
        db: Session,
        user_id: int,
        start_date: date,
        end_date: date
    ) -> List[dict]:
        """
        Get calendar overview for date range (default: 15 days before + 15 days after today)
        
        Shows which days have reminders and how many
        
        Args:
            db: Database session
            user_id: User ID
            start_date: Start date
            end_date: End date
            
        Returns:
            List of daily schedules with reminder counts
        """
        from datetime import timedelta
        
        # Get all active reminders
        reminders = db.query(MedicationReminder).filter(
            and_(
                MedicationReminder.user_id == user_id,
                MedicationReminder.is_active == True,
                or_(
                    MedicationReminder.end_date == None,
                    MedicationReminder.end_date >= start_date
                ),
                MedicationReminder.start_date <= end_date
            )
        ).all()
        
        # Build calendar
        calendar_days = []
        current_date = start_date
        
        while current_date <= end_date:
            times_set = set()
            reminder_count = 0
            
            # Check each reminder
            for reminder in reminders:
                if reminder.start_date.date() <= current_date <= (reminder.end_date.date() if reminder.end_date else date.max):
                    # Check if reminder applies on this day
                    applies = False
                    if reminder.frequency == "daily":
                        applies = True
                    elif reminder.frequency in ["weekly", "specific_days"]:
                        days_of_week = json.loads(reminder.days_of_week) if reminder.days_of_week else []
                        if current_date.weekday() in days_of_week:
                            applies = True
                    elif reminder.frequency == "every_other_day":
                        days_diff = (current_date - reminder.start_date.date()).days
                        if days_diff % 2 == 0:
                            applies = True
                    
                    if applies:
                        times_data = json.loads(reminder.times)
                        # Times are TimeSchedule objects: [{"time": "07:00", "period": "morning", "dosage": "2"}, ...]
                        reminder_count += len(times_data)
                        times_set.update([t['time'] for t in times_data])
            
            calendar_days.append({
                "date": current_date.isoformat(),
                "has_reminders": reminder_count > 0,
                "reminder_count": reminder_count,
                "times": sorted(list(times_set))
            })
            
            current_date += timedelta(days=1)
        
        return calendar_days
    
    @staticmethod
    def get_daily_schedule(
        db: Session,
        user_id: int,
        target_date: date
    ) -> dict:
        """
        Get detailed schedule for a specific day
        
        Returns all reminders grouped by time with taken status
        
        Args:
            db: Database session
            user_id: User ID
            target_date: Target date
            
        Returns:
            Daily schedule with reminder details and adherence status
        """
        from app.models.database import AdherenceLog
        from datetime import datetime, timedelta
        
        # Get all active reminders that apply on this date
        reminders = db.query(MedicationReminder).filter(
            and_(
                MedicationReminder.user_id == user_id,
                MedicationReminder.is_active == True,
                MedicationReminder.start_date <= datetime.combine(target_date, datetime.min.time()),
                or_(
                    MedicationReminder.end_date == None,
                    MedicationReminder.end_date >= datetime.combine(target_date, datetime.max.time())
                )
            )
        ).all()
        
        # Build schedule items
        schedules = []
        
        for reminder in reminders:
            times = json.loads(reminder.times)
            
            # Check if reminder applies on this day
            applies = False
            if reminder.frequency == "daily":
                applies = True
            elif reminder.frequency in ["weekly", "specific_days"]:
                days_of_week = json.loads(reminder.days_of_week) if reminder.days_of_week else []
                if target_date.weekday() in days_of_week:
                    applies = True
            elif reminder.frequency == "every_other_day":
                days_diff = (target_date - reminder.start_date.date()).days
                if days_diff % 2 == 0:
                    applies = True
            
            if not applies:
                continue
            
            # Parse times - they are TimeSchedule objects now
            times_data = json.loads(times)
            # times_data is list of dicts: [{"time": "07:00", "period": "morning", "dosage": "2"}, ...]
            
            for time_item in times_data:
                time_str = time_item['time']
                period = time_item.get('period')
                dosage_amount = time_item.get('dosage')
                
                # Build dosage info
                if dosage_amount and reminder.unit:
                    dosage_info = f"{dosage_amount} {reminder.unit}"
                elif dosage_amount:
                    dosage_info = dosage_amount
                else:
                    dosage_info = reminder.dosage
                
                # Check adherence status
                scheduled_datetime = datetime.combine(target_date, datetime.strptime(time_str, "%H:%M").time())
                
                # Find adherence log for this specific time
                log = db.query(AdherenceLog).filter(
                    and_(
                        AdherenceLog.reminder_id == reminder.id,
                        AdherenceLog.user_id == user_id,
                        AdherenceLog.scheduled_time >= scheduled_datetime,
                        AdherenceLog.scheduled_time < scheduled_datetime + timedelta(minutes=1)
                    )
                ).first()
                
                # Determine status
                if log:
                    status = log.action_type  # "taken", "snoozed", or "skipped"
                    is_taken = log.action_type == "taken"
                else:
                    status = "not_taken"
                    is_taken = False
                
                schedule_item = {
                    "reminder_id": reminder.id,
                    "medicine_name": reminder.medicine_name,
                    "time": time_str,
                    "dosage": dosage_info,
                    "status": status,
                    "is_taken": is_taken
                }
                
                # Add optional fields
                if reminder.unit:
                    schedule_item["unit"] = reminder.unit
                if reminder.meal_timing:
                    schedule_item["meal_timing"] = reminder.meal_timing
                if period:
                    schedule_item["period"] = period
                
                schedules.append(schedule_item)
        
        # Sort by time
        schedules.sort(key=lambda x: x["time"])
        
        return {
            "date": target_date.isoformat(),
            "total_reminders": len(schedules),
            "schedules": schedules
        }


# Create singleton instance
reminder_service = ReminderService()
