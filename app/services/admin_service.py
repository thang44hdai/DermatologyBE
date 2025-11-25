"""
Admin Service

Business logic for admin dashboard and system-wide statistics.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, extract, desc

from app.models.database import (
    MedicationReminder, 
    AdherenceLog, 
    User,
    Medicines
)

logger = logging.getLogger(__name__)


class AdminService:
    """Service for admin dashboard and analytics"""
    
    @staticmethod
    def get_dashboard_stats(db: Session) -> Dict[str, Any]:
        """
        Get overall system statistics
        
        Args:
            db: Database session
            
        Returns:
            Dictionary with system-wide stats
        """
        # Total counts
        total_users = db.query(func.count(User.id)).scalar()
        total_reminders = db.query(func.count(MedicationReminder.id)).scalar()
        active_reminders = db.query(func.count(MedicationReminder.id)).filter(
            MedicationReminder.is_active == True
        ).scalar()
        
        # Total adherence logs
        total_logs = db.query(func.count(AdherenceLog.id)).scalar()
        
        # Logs by type
        taken_count = db.query(func.count(AdherenceLog.id)).filter(
            AdherenceLog.action_type == 'taken'
        ).scalar()
        
        snoozed_count = db.query(func.count(AdherenceLog.id)).filter(
            AdherenceLog.action_type == 'snoozed'
        ).scalar()
        
        skipped_count = db.query(func.count(AdherenceLog.id)).filter(
            AdherenceLog.action_type == 'skipped'
        ).scalar()
        
        # Overall adherence rate
        adherence_rate = (taken_count / total_logs * 100) if total_logs > 0 else 0.0
        
        # Active users (users with active reminders)
        active_users = db.query(func.count(func.distinct(MedicationReminder.user_id))).filter(
            MedicationReminder.is_active == True
        ).scalar()
        
        return {
            "total_users": total_users,
            "active_users": active_users,
            "total_reminders": total_reminders,
            "active_reminders": active_reminders,
            "total_adherence_logs": total_logs,
            "taken_count": taken_count,
            "snoozed_count": snoozed_count,
            "skipped_count": skipped_count,
            "overall_adherence_rate": round(adherence_rate, 2)
        }
    
    @staticmethod
    def get_adherence_overview(
        db: Session,
        start_date: datetime,
        end_date: datetime
    ) -> List[Dict[str, Any]]:
        """
        Get adherence overview for a date range
        
        Args:
            db: Database session
            start_date: Start date
            end_date: End date
            
        Returns:
            List of daily adherence data
        """
        logs = db.query(
            func.date(AdherenceLog.scheduled_time).label('date'),
            AdherenceLog.action_type,
            func.count(AdherenceLog.id).label('count')
        ).filter(
            and_(
                AdherenceLog.scheduled_time >= start_date,
                AdherenceLog.scheduled_time <= end_date
            )
        ).group_by(
            func.date(AdherenceLog.scheduled_time),
            AdherenceLog.action_type
        ).all()
        
        # Organize by date
        date_data = {}
        for log in logs:
            date_str = log.date.isoformat()
            if date_str not in date_data:
                date_data[date_str] = {'date': date_str, 'taken': 0, 'snoozed': 0, 'skipped': 0}
            date_data[date_str][log.action_type] = log.count
        
        # Calculate adherence rate for each day
        result = []
        for date_str, data in sorted(date_data.items()):
            total = data['taken'] + data['snoozed'] + data['skipped']
            adherence_rate = (data['taken'] / total * 100) if total > 0 else 0
            result.append({
                **data,
                'total': total,
                'adherence_rate': round(adherence_rate, 2)
            })
        
        return result
    
    @staticmethod
    def get_user_engagement(
        db: Session,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Get user engagement metrics
        
        Args:
            db: Database session
            limit: Number of users to return
            
        Returns:
            List of user engagement data
        """
        # Get users with their reminder and adherence counts
        users = db.query(
            User.id,
            User.username,
            User.email,
            func.count(func.distinct(MedicationReminder.id)).label('reminder_count'),
            func.count(AdherenceLog.id).label('adherence_count'),
            func.max(AdherenceLog.created_at).label('last_activity')
        ).outerjoin(
            MedicationReminder, User.id == MedicationReminder.user_id
        ).outerjoin(
            AdherenceLog, User.id == AdherenceLog.user_id
        ).group_by(
            User.id
        ).order_by(
            desc('adherence_count')
        ).limit(limit).all()
        
        result = []
        for user in users:
            # Calculate adherence rate for this user
            if user.adherence_count > 0:
                taken = db.query(func.count(AdherenceLog.id)).filter(
                    and_(
                        AdherenceLog.user_id == user.id,
                        AdherenceLog.action_type == 'taken'
                    )
                ).scalar()
                adherence_rate = (taken / user.adherence_count * 100)
            else:
                adherence_rate = 0.0
            
            result.append({
                'user_id': user.id,
                'username': user.username,
                'email': user.email,
                'reminder_count': user.reminder_count,
                'adherence_count': user.adherence_count,
                'adherence_rate': round(adherence_rate, 2),
                'last_activity': user.last_activity.isoformat() if user.last_activity else None
            })
        
        return result
    
    @staticmethod
    def get_top_medicines(
        db: Session,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get most commonly used medicines
        
        Args:
            db: Database session
            limit: Number of medicines to return
            
        Returns:
            List of top medicines with usage counts
        """
        medicines = db.query(
            MedicationReminder.medicine_name,
            func.count(func.distinct(MedicationReminder.id)).label('reminder_count'),
            func.count(func.distinct(MedicationReminder.user_id)).label('user_count')
        ).group_by(
            MedicationReminder.medicine_name
        ).order_by(
            desc('reminder_count')
        ).limit(limit).all()
        
        result = []
        for med in medicines:
            result.append({
                'medicine_name': med.medicine_name,
                'reminder_count': med.reminder_count,
                'user_count': med.user_count
            })
        
        return result


# Create singleton instance
admin_service = AdminService()
