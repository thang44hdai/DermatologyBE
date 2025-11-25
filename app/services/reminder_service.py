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
        if reminder_data.frequency == 'weekly' and not reminder_data.days_of_week:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="days_of_week required for weekly frequency"
            )
        
        # Create reminder
        reminder = MedicationReminder(
            user_id=user_id,
            medicine_id=reminder_data.medicine_id,
            medicine_name=reminder_data.medicine_name,
            title=reminder_data.title,
            dosage=reminder_data.dosage,
            frequency=reminder_data.frequency,
            times=json.dumps(reminder_data.times),
            days_of_week=json.dumps(reminder_data.days_of_week) if reminder_data.days_of_week else None,
            start_date=reminder_data.start_date,
            end_date=reminder_data.end_date,
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
                setattr(reminder, field, json.dumps(value))
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


# Create singleton instance
reminder_service = ReminderService()
