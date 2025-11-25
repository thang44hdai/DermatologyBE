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
    AIAdviceRequest
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
    return ReminderResponse(
        id=reminder.id,
        user_id=reminder.user_id,
        medicine_id=reminder.medicine_id,
        medicine_name=reminder.medicine_name,
        title=reminder.title,
        dosage=reminder.dosage,
        frequency=reminder.frequency,
        times=json.loads(reminder.times),
        days_of_week=json.loads(reminder.days_of_week) if reminder.days_of_week else None,
        start_date=reminder.start_date,
        end_date=reminder.end_date,
        is_active=reminder.is_active,
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
        reminder_responses.append(ReminderResponse(
            id=r.id,
            user_id=r.user_id,
            medicine_id=r.medicine_id,
            medicine_name=r.medicine_name,
            title=r.title,
            dosage=r.dosage,
            frequency=r.frequency,
            times=json.loads(r.times),
            days_of_week=json.loads(r.days_of_week) if r.days_of_week else None,
            start_date=r.start_date,
            end_date=r.end_date,
            is_active=r.is_active,
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
    
    return ReminderResponse(
        id=reminder.id,
        user_id=reminder.user_id,
        medicine_id=reminder.medicine_id,
        medicine_name=reminder.medicine_name,
        title=reminder.title,
        dosage=reminder.dosage,
        frequency=reminder.frequency,
        times=json.loads(reminder.times),
        days_of_week=json.loads(reminder.days_of_week) if reminder.days_of_week else None,
        start_date=reminder.start_date,
        end_date=reminder.end_date,
        is_active=reminder.is_active,
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
    
    return ReminderResponse(
        id=reminder.id,
        user_id=reminder.user_id,
        medicine_id=reminder.medicine_id,
        medicine_name=reminder.medicine_name,
        title=reminder.title,
        dosage=reminder.dosage,
        frequency=reminder.frequency,
        times=json.loads(reminder.times),
        days_of_week=json.loads(reminder.days_of_week) if reminder.days_of_week else None,
        start_date=reminder.start_date,
        end_date=reminder.end_date,
        is_active=reminder.is_active,
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
    
    return ReminderResponse(
        id=reminder.id,
        user_id=reminder.user_id,
        medicine_id=reminder.medicine_id,
        medicine_name=reminder.medicine_name,
        title=reminder.title,
        dosage=reminder.dosage,
        frequency=reminder.frequency,
        times=json.loads(reminder.times),
        days_of_week=json.loads(reminder.days_of_week) if reminder.days_of_week else None,
        start_date=reminder.start_date,
        end_date=reminder.end_date,
        is_active=reminder.is_active,
        notes=reminder.notes,
        created_at=reminder.created_at,
        updated_at=reminder.updated_at,
        is_custom_medicine=(reminder.medicine_id is None)
    )


# ===== Adherence Tracking Endpoints =====

@router.post("/{reminder_id}/action", response_model=AdherenceLogResponse)
async def log_adherence_action(
    reminder_id: int,
    action: AdherenceAction,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Log user action on a reminder (taken/snoozed/skipped)
    
    Args:
        reminder_id: Reminder ID
        action_type: 'taken', 'snoozed', or 'skipped'
        snooze_minutes: Required if action_type is 'snoozed' (5-60)
        
    Note:
        scheduled_time is automatically set to current time
        
    Returns:
        Created adherence log
    """
    # Auto-generate scheduled_time as current time
    scheduled_time = datetime.now()
    
    log = adherence_service.log_action(
        db, reminder_id, current_user.id, action, scheduled_time
    )
    
    return AdherenceLogResponse(
        id=log.id,
        reminder_id=log.reminder_id,
        user_id=log.user_id,
        scheduled_time=log.scheduled_time,
        action_time=log.action_time,
        action_type=log.action_type,
        snooze_minutes=log.snooze_minutes,
        created_at=log.created_at
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


@router.get("/adherence/stats", response_model=AdherenceStats)
async def get_adherence_stats(
    year: int = Query(..., ge=2020, le=2100, description="Year"),
    month: int = Query(..., ge=1, le=12, description="Month (1-12)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get monthly adherence statistics
    
    Args:
        year: Year (e.g., 2025)
        month: Month (1-12)
        
    Returns:
        Monthly statistics including adherence rate
    """
    stats = adherence_service.get_monthly_stats(db, current_user.id, year, month)
    return stats


@router.get("/adherence/chart", response_model=list[AdherenceChartData])
async def get_adherence_chart(
    year: int = Query(..., ge=2020, le=2100, description="Year"),
    month: int = Query(..., ge=1, le=12, description="Month (1-12)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get daily adherence data for chart visualization
    
    Args:
        year: Year
        month: Month (1-12)
        
    Returns:
        Daily breakdown with taken/snoozed/skipped counts
    """
    chart_data = adherence_service.get_chart_data(db, current_user.id, year, month)
    return chart_data


# ===== AI Advice Endpoints =====

@router.get("/{reminder_id}/advice", response_model=AIAdvice)
async def get_reminder_advice(
    reminder_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get AI-generated personalized advice based on adherence behavior
    
    Analyzes the last 30 days of adherence data (taken/snoozed/skipped)
    and provides personalized recommendations
    
    Args:
        reminder_id: Reminder ID
        
    Returns:
        Personalized advice based on adherence patterns
    """
    from app.services.ai_advice_service import ai_advice_service
    
    # Generate advice based on adherence behavior
    advice = await ai_advice_service.generate_advice_for_reminder(
        db=db,
        reminder_id=reminder_id,
        user_id=current_user.id
    )
    
    return advice



