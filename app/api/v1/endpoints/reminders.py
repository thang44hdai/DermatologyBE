"""
Medication Reminder API Endpoints

Endpoints for managing medication reminders and adherence tracking.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
import json

from app.core.dependencies import get_db, get_current_user
from app.services.reminder_service import reminder_service
from app.services.adherence_service import adherence_service
from app.schemas.reminder import (
    ReminderCreate,
    ReminderUpdate,
    ReminderResponse,
    ReminderListResponse,
    AdherenceAction,
    AdherenceLogResponse,
    AdherenceStats,
    AdherenceChartData,
    AIAdvice,
    AIAdviceRequest,
    CalendarMonthOverview,
    CalendarDaySchedule,
    DailyScheduleDetail
)
from app.models.database import User

router = APIRouter()


# ===== Reminder CRUD Endpoints =====

@router.post("/", response_model=ReminderResponse, status_code=status.HTTP_201_CREATED)
async def create_reminder(
    reminder_data: ReminderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new medication reminder
    
    Args:
        medicine_id: Optional ID from medicines table
        medicine_name: Required medicine name (custom or from DB)
        title: Reminder title/description
        dosage: Dosage information
        frequency: 'daily', 'weekly', or 'custom'
        times: Array of times in HH:MM format
        days_of_week: For weekly - [0-6] where 0=Monday
        start_date: Start date
        end_date: Optional end date
        notes: Additional notes
        
    Returns:
        Created reminder information
    """
    reminder = reminder_service.create_reminder(db, reminder_data, current_user.id)
    
    # Parse JSON fields for response
    times_data = json.loads(reminder.times)
    # times_data is always new format from create (TimeSchedule objects)
    return ReminderResponse(
        id=reminder.id,
        user_id=reminder.user_id,
        medicine_id=reminder.medicine_id,
        medicine_name=reminder.medicine_name,
        dosage=reminder.dosage,
        unit=reminder.unit,
        meal_timing=reminder.meal_timing,
        frequency=reminder.frequency,
        times=times_data,
        days_of_week=json.loads(reminder.days_of_week) if reminder.days_of_week else None,
        start_date=reminder.start_date,
        end_date=reminder.end_date,
        is_active=reminder.is_active,
        is_notification_enabled=reminder.is_notification_enabled,
        notes=reminder.notes,
        created_at=reminder.created_at,
        updated_at=reminder.updated_at,
        is_custom_medicine=(reminder.medicine_id is None)
    )


@router.get("/", response_model=ReminderListResponse)
async def get_reminders(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of records"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    frequency: Optional[str] = Query(None, description="Filter by frequency"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get user's medication reminders with optional filters
    
    Args:
        skip: Pagination offset
        limit: Max results (max 100)
        is_active: Filter active/inactive
        frequency: Filter by daily/weekly/custom
        
    Returns:
        List of reminders with pagination info
    """
    reminders, total = reminder_service.get_reminders(
        db, current_user.id, skip, limit, is_active, frequency
    )
    
    # Convert to response models
    reminder_responses = []
    for r in reminders:
        times_data = json.loads(r.times)
        # Handle backward compatibility: convert old format to new format
        if times_data and isinstance(times_data[0], str):
            # Old format: ["09:00", "14:00"]
            # Convert to new format with default values
            times_data = [
                {"time": t, "period": "morning", "dosage": "1"}
                for t in times_data
            ]
        
        reminder_responses.append(ReminderResponse(
            id=r.id,
            user_id=r.user_id,
            medicine_id=r.medicine_id,
            medicine_name=r.medicine_name,
            dosage=r.dosage,
            unit=r.unit,
            meal_timing=r.meal_timing,
            frequency=r.frequency,
            times=times_data,
            days_of_week=json.loads(r.days_of_week) if r.days_of_week else None,
            start_date=r.start_date,
            end_date=r.end_date,
            is_active=r.is_active,
            is_notification_enabled=r.is_notification_enabled,
            notes=r.notes,
            created_at=r.created_at,
            updated_at=r.updated_at,
            is_custom_medicine=(r.medicine_id is None)
        ))
    
    return ReminderListResponse(
        reminders=reminder_responses,
        total=total,
        skip=skip,
        limit=limit
    )


# ===== Calendar View Endpoints =====
# IMPORTANT: These must come BEFORE /{reminder_id} to avoid routing conflicts

@router.get("/calendar", response_model=CalendarMonthOverview)
async def get_calendar_overview(
    week_offset: int = Query(0, description="Week offset from current week (0=this week, -1=last week, 1=next week)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get weekly calendar overview of medication schedule (Monday-Sunday)
    
    Args:
        week_offset: Week offset from current week (default: 0 for this week)
    
    Returns:
        Calendar overview with daily reminder counts for the week
    """
    from datetime import date, timedelta
    
    # Get Monday of the target week
    today = date.today()
    # today.weekday(): 0=Monday, 6=Sunday
    days_since_monday = today.weekday()
    this_monday = today - timedelta(days=days_since_monday)
    
    # Apply week offset
    target_monday = this_monday + timedelta(weeks=week_offset)
    target_sunday = target_monday + timedelta(days=6)
    
    # Get calendar data
    days = reminder_service.get_calendar_overview(
        db=db,
        user_id=current_user.id,
        start_date=target_monday,
        end_date=target_sunday
    )
    
    return CalendarMonthOverview(
        start_date=target_monday.isoformat(),
        end_date=target_sunday.isoformat(),
        days=days
    )


@router.get("/calendar/{target_date}", response_model=DailyScheduleDetail)
async def get_daily_schedule(
    target_date: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get detailed schedule for a specific day
    
    Returns all reminders for the day grouped by time, with taken status
    
    Args:
        target_date: Date in YYYY-MM-DD format
        
    Returns:
        Detailed daily schedule with adherence status
    """
    try:
        target = datetime.strptime(target_date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid date format. Use YYYY-MM-DD"
        )
    
    return reminder_service.get_daily_schedule(
        db=db,
        user_id=current_user.id,
        target_date=target
    )


@router.get("/{reminder_id}", response_model=ReminderResponse)
async def get_reminder(
    reminder_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a specific reminder by ID
    
    Args:
        reminder_id: Reminder ID
        
    Returns:
        Reminder information
    """
    reminder = reminder_service.get_reminder(db, reminder_id, current_user.id)
    
    times_data = json.loads(reminder.times)
    # Handle backward compatibility
    if times_data and isinstance(times_data[0], str):
        times_data = [
            {"time": t, "period": "morning", "dosage": "1"}
            for t in times_data
        ]
    
    return ReminderResponse(
        id=reminder.id,
        user_id=reminder.user_id,
        medicine_id=reminder.medicine_id,
        medicine_name=reminder.medicine_name,
        dosage=reminder.dosage,
        unit=reminder.unit,
        meal_timing=reminder.meal_timing,
        frequency=reminder.frequency,
        times=times_data,
        days_of_week=json.loads(reminder.days_of_week) if reminder.days_of_week else None,
        start_date=reminder.start_date,
        end_date=reminder.end_date,
        is_active=reminder.is_active,
        is_notification_enabled=reminder.is_notification_enabled,
        notes=reminder.notes,
        created_at=reminder.created_at,
        updated_at=reminder.updated_at,
        is_custom_medicine=(reminder.medicine_id is None)
    )


@router.put("/{reminder_id}", response_model=ReminderResponse)
async def update_reminder(
    reminder_id: int,
    update_data: ReminderUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update a medication reminder
    
    Args:
        reminder_id: Reminder ID to update
        
    Body: Fields to update (all optional):
        - title: Reminder title
        - dosage: Dosage information
        - times: Array of times
        - days_of_week: Days for weekly reminders
        - end_date: End date
        - is_active: Active status
        - notes: Notes
        
    Returns:
        Updated reminder information
    """
    reminder = reminder_service.update_reminder(
        db, reminder_id, current_user.id, update_data
    )
    
    times_data = json.loads(reminder.times)
    # Handle backward compatibility
    if times_data and isinstance(times_data[0], str):
        times_data = [
            {"time": t, "period": "morning", "dosage": "1"}
            for t in times_data
        ]
    
    return ReminderResponse(
        id=reminder.id,
        user_id=reminder.user_id,
        medicine_id=reminder.medicine_id,
        medicine_name=reminder.medicine_name,
        dosage=reminder.dosage,
        unit=reminder.unit,
        meal_timing=reminder.meal_timing,
        frequency=reminder.frequency,
        times=times_data,
        days_of_week=json.loads(reminder.days_of_week) if reminder.days_of_week else None,
        start_date=reminder.start_date,
        end_date=reminder.end_date,
        is_active=reminder.is_active,
        is_notification_enabled=reminder.is_notification_enabled,
        notes=reminder.notes,
        created_at=reminder.created_at,
        updated_at=reminder.updated_at,
        is_custom_medicine=(reminder.medicine_id is None)
    )


@router.delete("/{reminder_id}")
async def delete_reminder(
    reminder_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a medication reminder
    
    Args:
        reminder_id: Reminder ID to delete
        
    Returns:
        Success message
    """
    reminder_service.delete_reminder(db, reminder_id, current_user.id)
    
    return {
        "success": True,
        "message": "Reminder deleted successfully",
        "reminder_id": reminder_id
    }


@router.post("/{reminder_id}/toggle", response_model=ReminderResponse)
async def toggle_reminder(
    reminder_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Toggle reminder active status (enable/disable)
    
    Args:
        reminder_id: Reminder ID
        
    Returns:
        Updated reminder with toggled status
    """
    reminder = reminder_service.toggle_reminder(db, reminder_id, current_user.id)
    
    times_data = json.loads(reminder.times)
    # Handle backward compatibility
    if times_data and isinstance(times_data[0], str):
        times_data = [
            {"time": t, "period": "morning", "dosage": "1"}
            for t in times_data
        ]
    
    return ReminderResponse(
        id=reminder.id,
        user_id=reminder.user_id,
        medicine_id=reminder.medicine_id,
        medicine_name=reminder.medicine_name,
        dosage=reminder.dosage,
        unit=reminder.unit,
        meal_timing=reminder.meal_timing,
        frequency=reminder.frequency,
        times=times_data,
        days_of_week=json.loads(reminder.days_of_week) if reminder.days_of_week else None,
        start_date=reminder.start_date,
        end_date=reminder.end_date,
        is_active=reminder.is_active,
        is_notification_enabled=reminder.is_notification_enabled,
        notes=reminder.notes,
        created_at=reminder.created_at,
        updated_at=reminder.updated_at,
        is_custom_medicine=(reminder.medicine_id is None)
    )


# ===== Adherence Tracking Endpoints =====

@router.post("/{reminder_id}/toggle-taken", response_model=AdherenceLogResponse)
async def toggle_medication_taken(
    reminder_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Toggle medication taken status for the most recent past medication time today
    
    Automatically finds the most recent medication time that has passed and toggles it.
    If no medication time has passed yet today, returns 400 error.
    
    Args:
        reminder_id: Reminder ID
        
    Returns:
        Updated or created adherence log
    """
    from app.models.database import AdherenceLog, MedicationReminder
    from sqlalchemy import and_
    from datetime import timedelta, date
    import json
    
    # Get the reminder
    reminder = db.query(MedicationReminder).filter(
        and_(
            MedicationReminder.id == reminder_id,
            MedicationReminder.user_id == current_user.id
        )
    ).first()
    
    if not reminder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reminder not found"
        )
    
    # Get current time and today's date
    now = datetime.now()
    today = now.date()
    
    # Check if reminder applies today
    if reminder.start_date.date() > today or (reminder.end_date and reminder.end_date.date() < today):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reminder is not active today"
        )
    
    # Check frequency
    applies_today = False
    if reminder.frequency == "daily":
        applies_today = True
    elif reminder.frequency in ["weekly", "specific_days"]:
        days_of_week = json.loads(reminder.days_of_week) if reminder.days_of_week else []
        if today.weekday() in days_of_week:
            applies_today = True
    elif reminder.frequency == "every_other_day":
        days_diff = (today - reminder.start_date.date()).days
        if days_diff % 2 == 0:
            applies_today = True
    
    if not applies_today:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No medication scheduled for today"
        )
    
    # Parse times from reminder
    times_data = json.loads(reminder.times)
    # times_data is list of dicts: [{"time": "07:00", "period": "morning", "dosage": "2"}, ...]
    
    # Find the most recent time that has passed
    scheduled_time = None
    current_time_str = now.strftime("%H:%M")
    
    for time_item in times_data:
        time_str = time_item['time']
        if time_str <= current_time_str:
            # This time has passed
            if scheduled_time is None or time_str > scheduled_time.strftime("%H:%M"):
                # Parse to datetime
                time_parts = time_str.split(":")
                scheduled_time = datetime.combine(today, datetime.strptime(time_str, "%H:%M").time())
    
    if scheduled_time is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No medication time has passed yet today"
        )
    
    # Check if log already exists for this scheduled time
    existing_log = db.query(AdherenceLog).filter(
        and_(
            AdherenceLog.reminder_id == reminder_id,
            AdherenceLog.user_id == current_user.id,
            AdherenceLog.scheduled_time >= scheduled_time,
            AdherenceLog.scheduled_time < scheduled_time + timedelta(minutes=1)
        )
    ).first()
    
    if existing_log:
        # Toggle: if it was taken, mark as not taken (delete)
        if existing_log.action_type == "taken":
            db.delete(existing_log)
            db.commit()
            # Return response indicating not_taken
            return AdherenceLogResponse(
                id=0,
                reminder_id=reminder_id,
                user_id=current_user.id,
                scheduled_time=scheduled_time,
                action_time=None,
                action_type="not_taken",
                snooze_minutes=None,
                created_at=now
            )
        else:
            # If it was not_taken or other, mark as taken
            existing_log.action_type = "taken"
            existing_log.action_time = now
            db.commit()
            db.refresh(existing_log)
            return AdherenceLogResponse(
                id=existing_log.id,
                reminder_id=existing_log.reminder_id,
                user_id=existing_log.user_id,
                scheduled_time=existing_log.scheduled_time,
                action_time=existing_log.action_time,
                action_type=existing_log.action_type,
                snooze_minutes=existing_log.snooze_minutes,
                created_at=existing_log.created_at
            )
    else:
        # No existing log, create new one as taken
        new_log = AdherenceLog(
            reminder_id=reminder_id,
            user_id=current_user.id,
            scheduled_time=scheduled_time,
            action_time=now,
            action_type="taken",
            snooze_minutes=None
        )
        db.add(new_log)
        db.commit()
        db.refresh(new_log)
        
        return AdherenceLogResponse(
            id=new_log.id,
            reminder_id=new_log.reminder_id,
            user_id=new_log.user_id,
            scheduled_time=new_log.scheduled_time,
            action_time=new_log.action_time,
            action_type=new_log.action_type,
            snooze_minutes=new_log.snooze_minutes,
            created_at=new_log.created_at
        )


@router.get("/{reminder_id}/adherence", response_model=list[AdherenceLogResponse])
async def get_adherence_logs(
    reminder_id: int,
    limit: int = Query(100, ge=1, le=500, description="Max number of logs"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get adherence logs for a specific reminder
    
    Args:
        reminder_id: Reminder ID
        limit: Maximum number of logs (max 500)
        
    Returns:
        List of adherence logs
    """
    logs = adherence_service.get_adherence_logs(
        db, reminder_id, current_user.id, limit
    )
    
    return [
        AdherenceLogResponse(
            id=log.id,
            reminder_id=log.reminder_id,
            user_id=log.user_id,
            scheduled_time=log.scheduled_time,
            action_time=log.action_time,
            action_type=log.action_type,
            snooze_minutes=log.snooze_minutes,
            created_at=log.created_at
        )
        for log in logs
    ]


# ===== AI Advice Endpoints =====
# REMOVED - AI advice endpoint removed per user request
