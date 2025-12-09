"""
User API Endpoints - Enhanced with FCM token support
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel, Field

from app.core.dependencies import get_db, get_current_active_user, get_current_admin
from app.schemas.user import UserCreate, UserResponse, UserRoleUpdate
from app.services.user_service import UserService
from app.models.database import User

router = APIRouter()


class FCMTokenUpdate(BaseModel):
    """Schema for FCM token registration"""
    fcm_token: str = Field(..., min_length=1, max_length=255, description="Firebase Cloud Messaging token")


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    """
    Create a new user (Public endpoint for registration)
    
    Note: For authenticated registration, use /api/v1/auth/register
    New users get 'user' role by default
    """
    return UserService.create_user(db=db, user=user)


@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get user by ID (Protected - requires authentication)
    
    Users can view their own profile or any profile if they're logged in
    """
    db_user = UserService.get_user(db=db, user_id=user_id)
    if db_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return db_user


@router.get("/", response_model=List[UserResponse])
def get_users(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)  # Admin only
):
    """
    Get list of users (Protected - Admin only)
    
    Only administrators can view the full list of users
    """
    users = UserService.get_users(db=db, skip=skip, limit=limit)
    return users


@router.delete("/{user_id}")
def delete_user(
    user_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Delete a user (Protected)
    
    - Users can delete their own account
    - Admins can delete any account
    """
    # Check if user is admin or deleting their own account
    from app.models.database import UserRole
    
    if current_user.role != UserRole.ADMIN and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this user. You can only delete your own account."
        )
    
    UserService.delete_user(db=db, user_id=user_id)
    return {"message": "User deleted successfully"}


@router.put("/{user_id}/role", response_model=UserResponse)
def update_user_role(
    user_id: int,
    role_update: UserRoleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)  # Admin only
):
    """
    Update user role (Protected - Admin only)
    
    Only administrators can promote/demote users
    
    - **role**: 'user' or 'admin'
    """
    # Prevent admin from demoting themselves
    if current_user.id == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot change your own role"
        )
    
    updated_user = UserService.update_user_role(db, user_id, role_update.role)
    return updated_user


@router.post("/fcm-token", status_code=status.HTTP_200_OK)
def register_fcm_token(
    token_data: FCMTokenUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Register or update FCM token for push notifications
    
    **FCM Token** là device token duy nhất từ Firebase cho mỗi thiết bị.
    Mobile app sử dụng Firebase SDK để lấy token và gửi lên đây.
    
    Args:
        fcm_token: Firebase Cloud Messaging device token
        
    Returns:
        Success message
        
    Example (Flutter):
        ```dart
        String? token = await FirebaseMessaging.instance.getToken();
        await api.post('/users/fcm-token', {'fcm_token': token});
        ```
    """
    # Update user's FCM token
    current_user.fcm_token = token_data.fcm_token
    db.commit()
    
    return {
        "success": True,
        "message": "FCM token registered successfully",
        "user_id": current_user.id
    }


@router.delete("/fcm-token", status_code=status.HTTP_200_OK)
def unregister_fcm_token(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Unregister FCM token (e.g., on logout)
    
    Returns:
        Success message
    """
    current_user.fcm_token = None
    db.commit()
    
    return {
        "success": True,
        "message": "FCM token unregistered successfully"
    }


@router.post("/test-notification", status_code=status.HTTP_200_OK)
async def send_test_notification(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Gửi thông báo test để kiểm tra FCM
    
    Dùng endpoint này để verify rằng:
    - FCM token đã được đăng ký đúng
    - Firebase SDK hoạt động bình thường
    - App có thể nhận push notification
    
    Returns:
        Success message nếu gửi thành công
        
    Raises:
        400: Nếu chưa đăng ký FCM token
        500: Nếu gửi thông báo thất bại
    """
    from app.services.notification_service import notification_service
    from datetime import datetime
    
    if not current_user.fcm_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Chưa đăng ký FCM token. Vui lòng đăng ký trước bằng endpoint POST /users/fcm-token"
        )
    
    # Gửi thông báo test
    success = await notification_service.send_reminder_notification(
        user_id=current_user.id,
        reminder_id=0,  # Test notification, không liên kết reminder
        title="🔔 Thông Báo Test",
        body="Hệ thống thông báo đang hoạt động bình thường! ✅",
        scheduled_time=datetime.now()
    )
    
    if success:
        return {
            "success": True,
            "message": "Đã gửi thông báo test thành công. Kiểm tra điện thoại của bạn!"
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Gửi thông báo thất bại. FCM token có thể đã hết hạn. Thử đăng ký lại token."
        )
