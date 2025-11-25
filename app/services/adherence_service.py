"""
Adherence Service

Business logic for tracking medication adherence.
"""

import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, func, extract
from fastapi import HTTPException, status

from app.models.database import AdherenceLog, MedicationReminder
from app.schemas.reminder import (
    AdherenceAction,
    AdherenceLogResponse, 
    AdherenceStats,
    AdherenceChartData
)

logger = logging.getLogger(__name__)


class AdherenceService:
    """Service class for adherence tracking operations"""
    
    @staticmethod
    def log_action(
        db: Session,
        reminder_id: int,
        user_id: int,
        action: AdherenceAction,
        scheduled_time: datetime
    ) -> AdherenceLog:
        """
        Log user action for a medication reminder
        
        Args:
            db: Database session
            reminder_id: Reminder ID
            user_id: User ID
            action: User action (taken/snoozed/skipped)
            scheduled_time: When the reminder was scheduled
            
        Returns:
            Created AdherenceLog object
            
        Raises:
            HTTPException: If reminder not found or doesn't belong to user
        """
        # Verify reminder exists and belongs to user
        reminder = db.query(MedicationReminder).filter(
            and_(
                MedicationReminder.id == reminder_id,
                MedicationReminder.user_id == user_id
            )
        ).first()
        
        if not reminder:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Reminder not found"
            )
        
        # Create adherence log
        log = AdherenceLog(
            reminder_id=reminder_id,
            user_id=user_id,
            scheduled_time=scheduled_time,
            action_time=datetime.now(),
            action_type=action.action_type,
            snooze_minutes=action.snooze_minutes
        )
        
        db.add(log)
        db.commit()
        db.refresh(log)
        
        logger.info(f"Logged {action.action_type} action for reminder {reminder_id} by user {user_id}")
        return log
    
    @staticmethod
    def get_adherence_logs(
        db: Session,
        reminder_id: int,
        user_id: int,
        limit: int = 100
    ) -> List[AdherenceLog]:
        """
        Get adherence logs for a specific reminder
        
        Args:
            db: Database session
            reminder_id: Reminder ID
            user_id: User ID (for authorization)
            limit: Maximum number of logs
            
        Returns:
            List of AdherenceLog objects
        """
        # Verify ownership
        reminder = db.query(MedicationReminder).filter(
            and_(
                MedicationReminder.id == reminder_id,
                MedicationReminder.user_id == user_id
            )
        ).first()
        
        if not reminder:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Reminder not found"
            )
        
        logs = db.query(AdherenceLog).filter(
            AdherenceLog.reminder_id == reminder_id
        ).order_by(
            AdherenceLog.scheduled_time.desc()
        ).limit(limit).all()
        
        return logs
    
    @staticmethod
    def get_monthly_stats(
        db: Session,
        user_id: int,
        year: int,
        month: int
    ) -> AdherenceStats:
        """
        Calculate monthly adherence statistics for a user
        
        Args:
            db: Database session
            user_id: User ID
            year: Year (e.g., 2025)
            month: Month (1-12)
            
        Returns:
            AdherenceStats object
        """
        # Query logs for the month
        logs = db.query(AdherenceLog).filter(
            and_(
                AdherenceLog.user_id == user_id,
                extract('year', AdherenceLog.scheduled_time) == year,
                extract('month', AdherenceLog.scheduled_time) == month
            )
        ).all()
        
        # Calculate stats
        total_scheduled = len(logs)
        total_taken = sum(1 for log in logs if log.action_type == 'taken')
        total_snoozed = sum(1 for log in logs if log.action_type == 'snoozed')
        total_skipped = sum(1 for log in logs if log.action_type == 'skipped')
        
        # Calculate adherence rate (taken / total)
        adherence_rate = (total_taken / total_scheduled * 100) if total_scheduled > 0 else 0.0
        
        return AdherenceStats(
            month=f"{year}-{month:02d}",
            total_scheduled=total_scheduled,
            total_taken=total_taken,
            total_snoozed=total_snoozed,
            total_skipped=total_skipped,
            adherence_rate=round(adherence_rate, 2)
        )
    
    @staticmethod
    def get_chart_data(
        db: Session,
        user_id: int,
        year: int,
        month: int
    ) -> List[AdherenceChartData]:
        """
        Get daily adherence data for chart visualization
        
        Args:
            db: Database session
            user_id: User ID
            year: Year
            month: Month (1-12)
            
        Returns:
            List of AdherenceChartData for each day
        """
        from calendar import monthrange
        
        # Get logs for the month
        logs = db.query(AdherenceLog).filter(
            and_(
                AdherenceLog.user_id == user_id,
                extract('year', AdherenceLog.scheduled_time) == year,
                extract('month', AdherenceLog.scheduled_time) == month
            )
        ).all()
        
        # Group by day
        daily_data: Dict[int, Dict[str, int]] = {}
        for log in logs:
            day = log.scheduled_time.day
            if day not in daily_data:
                daily_data[day] = {'taken': 0, 'snoozed': 0, 'skipped': 0}
            daily_data[day][log.action_type] += 1
        
        # Generate chart data for all days in month
        days_in_month = monthrange(year, month)[1]
        chart_data = []
        
        for day in range(1, days_in_month + 1):
            data = daily_data.get(day, {'taken': 0, 'snoozed': 0, 'skipped': 0})
            chart_data.append(AdherenceChartData(
                date=f"{year}-{month:02d}-{day:02d}",
                taken=data['taken'],
                snoozed=data['snoozed'],
                skipped=data['skipped']
            ))
        
        return chart_data


# Create singleton instance
adherence_service = AdherenceService()
