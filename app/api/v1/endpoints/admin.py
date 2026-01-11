"""
Admin Dashboard API Endpoints

Endpoints for admin dashboard and system-wide analytics.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app.core.dependencies import get_db, get_current_admin
from app.services.admin_service import admin_service
from app.models import User

router = APIRouter()


@router.get("/dashboard/stats")
async def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """
    Get overall system statistics
    
    **Admin only endpoint**
    
    Returns:
        - Total users
        - Active users (with active reminders)
        - Total reminders
        - Active reminders
        - Adherence statistics
        - Overall adherence rate
    """
    stats = admin_service.get_dashboard_stats(db)
    return stats


@router.get("/dashboard/adherence-overview")
async def get_adherence_overview(
    start_date: datetime = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: datetime = Query(None, description="End date (YYYY-MM-DD), defaults to today"),
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """
    Get adherence overview for a date range
    
    **Admin only endpoint**
    
    Args:
        start_date: Start date
        end_date: End date (optional, defaults to today)
        
    Returns:
        Daily breakdown with taken/snoozed/skipped counts and adherence rates
    """
    if not end_date:
        end_date = datetime.now()
    
    overview = admin_service.get_adherence_overview(db, start_date, end_date)
    return {
        "start_date": start_date.date().isoformat(),
        "end_date": end_date.date().isoformat(),
        "data": overview
    }


@router.get("/dashboard/user-engagement")
async def get_user_engagement(
    limit: int = Query(20, ge=1, le=100, description="Number of top users to return"),
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """
    Get user engagement metrics
    
    **Admin only endpoint**
    
    Args:
        limit: Number of top users to return (max 100)
        
    Returns:
        List of users ordered by engagement with:
        - Reminder count
        - Adherence count
        - Adherence rate
        - Last activity
    """
    engagement = admin_service.get_user_engagement(db, limit)
    return {
        "total_users": len(engagement),
        "users": engagement
    }


@router.get("/dashboard/top-medicines")
async def get_top_medicines(
    limit: int = Query(10, ge=1, le=50, description="Number of top medicines"),
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """
    Get most commonly used medicines
    
    **Admin only endpoint**
    
    Args:
        limit: Number of medicines to return (max 50)
        
    Returns:
        List of medicines with:
        - Reminder count
        - User count
    """
    medicines = admin_service.get_top_medicines(db, limit)
    return {
        "total": len(medicines),
        "medicines": medicines
    }
