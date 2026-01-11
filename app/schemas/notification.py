from pydantic import BaseModel, Field

class FCMTokenRequest(BaseModel):
    """Request để đăng ký FCM token"""
    fcm_token: str = Field(..., min_length=1, description="Firebase Cloud Messaging device token")
    
    class Config:
        json_schema_extra = {
            "example": {
                "fcm_token": "dXy4Z1k2M3pQ5r6S7t8U9v0W1x2Y3..."
            }
        }
