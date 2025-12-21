"""
Notification Service

Service for sending push notifications via Firebase Cloud Messaging.
"""

import logging
from datetime import datetime
from typing import Optional
import firebase_admin
from firebase_admin import credentials, messaging

from app.config.settings import settings

logger = logging.getLogger(__name__)


class NotificationService:
    """Service for sending push notifications"""
    
    def __init__(self):
        self.initialized = False
        self.firebase_app = None
    
    def initialize(self):
        """Initialize Firebase Admin SDK"""
        try:
            if not self.initialized:
                # Check if Firebase is already initialized
                try:
                    self.firebase_app = firebase_admin.get_app()
                    logger.info("Firebase already initialized")
                except ValueError:
                    # Initialize Firebase
                    cred = credentials.Certificate(settings.FIREBASE_SERVICE_ACCOUNT_KEY)
                    self.firebase_app = firebase_admin.initialize_app(cred)
                    logger.info("✅ Firebase Admin SDK initialized")
                
                self.initialized = True
        
        except Exception as e:
            logger.error(f"Failed to initialize Firebase: {e}")
            self.initialized = False
    
    async def send_reminder_notification(
        self,
        user_id: int,
        reminder_id: int,
        title: str,
        body: str,
        scheduled_time: datetime
    ) -> bool:
        """
        Send reminder push notification to user
        
        Args:
            user_id: User ID
            reminder_id: Reminder ID
            title: Notification title
            body: Notification body
            scheduled_time: When the reminder was scheduled
            
        Returns:
            True if sent successfully, False otherwise
        """
        if not self.initialized:
            self.initialize()
        
        if not self.initialized:
            logger.error("Firebase not initialized, cannot send notification")
            return False
        
        try:
            # Import here to avoid circular dependency
            from app.db.session import SessionLocal
            from app.models import User
            
            # Get user's FCM token from database
            db = SessionLocal()
            try:
                user = db.query(User).filter(User.id == user_id).first()
                if not user or not user.fcm_token:
                    logger.warning(f"User {user_id} has no FCM token registered")
                    return False
                
                user_fcm_token = user.fcm_token
            finally:
                db.close()
            
            # Create notification message
            message = messaging.Message(
                notification=messaging.Notification(
                    title=title,
                    body=body
                ),
                data={
                    'type': 'medication_reminder',
                    'reminder_id': str(reminder_id),
                    'scheduled_time': scheduled_time.isoformat()
                },
                token=user_fcm_token
            )
            
            # Send notification
            try:
                response = messaging.send(message)
                logger.info(f"✅ Notification sent to user {user_id}: {response}")
                return True
            
            except messaging.UnregisteredError:
                # Token không hợp lệ hoặc đã hết hạn
                logger.warning(f"⚠️ FCM token của user {user_id} không hợp lệ, đang xóa...")
                
                # Tự động xóa token khỏi database
                db_cleanup = SessionLocal()
                try:
                    user = db_cleanup.query(User).filter(User.id == user_id).first()
                    if user:
                        user.fcm_token = None
                        db_cleanup.commit()
                        logger.info(f"Đã xóa FCM token của user {user_id}")
                finally:
                    db_cleanup.close()
                
                return False
            
            except Exception as send_error:
                logger.error(f"❌ Lỗi khi gửi thông báo: {send_error}")
                return False
        
        except Exception as e:
            logger.error(f"Error sending notification: {e}")
            return False
    
    async def send_bulk_notifications(
        self,
        tokens: list[str],
        title: str,
        body: str,
        data: Optional[dict] = None
    ) -> dict:
        """
        Send notification to multiple devices
        
        Args:
            tokens: List of FCM tokens
            title: Notification title
            body: Notification body
            data: Optional data payload
            
        Returns:
            Dictionary with success_count and failure_count
        """
        if not self.initialized:
            self.initialize()
        
        if not self.initialized or not tokens:
            return {'success_count': 0, 'failure_count': 0}
        
        try:
            message = messaging.MulticastMessage(
                notification=messaging.Notification(
                    title=title,
                    body=body
                ),
                data=data or {},
                tokens=tokens
            )
            
            response = messaging.send_multicast(message)
            
            logger.info(f"Sent {response.success_count} notifications, {response.failure_count} failures")
            
            return {
                'success_count': response.success_count,
                'failure_count': response.failure_count
            }
        
        except Exception as e:
            logger.error(f"Error sending bulk notifications: {e}")
            return {'success_count': 0, 'failure_count': len(tokens)}


# Create singleton instance
notification_service = NotificationService()
