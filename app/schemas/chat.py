from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime


class ChatRequest(BaseModel):
    """
    Request model for chat endpoint.
    """
    session_id: Optional[str] = Field(
        None,
        description="UUID of the chat session. If null, a new session will be created."
    )
    message: str = Field(
        ...,
        min_length=1,
        description="The user's question or message."
    )

    @validator('message')
    def message_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Message cannot be empty or whitespace only')
        return v.strip()

    @validator('session_id')
    def validate_session_id(cls, v):
        if v is not None and not v.strip():
            raise ValueError('Session ID cannot be empty string')
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "550e8400-e29b-41d4-a716-446655440000",
                "message": "Tôi bị đau đầu, nên uống thuốc gì?"
            }
        }


class ChatResponse(BaseModel):
    """
    Response model for chat endpoint.
    """
    session_id: str = Field(
        ...,
        description="UUID of the chat session."
    )
    message: str = Field(
        ...,
        description="The AI assistant's response."
    )
    sources: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="List of product/medicine metadata used for RAG (Retrieval-Augmented Generation)."
    )
    created_at: datetime = Field(
        ...,
        description="Timestamp when the response was created."
    )

    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "550e8400-e29b-41d4-a716-446655440000",
                "message": "Bạn có thể sử dụng Paracetamol để giảm đau đầu...",
                "sources": [
                    {
                        "medicine_id": 123,
                        "name": "Paracetamol 500mg",
                        "price": 15000,
                        "image_url": "https://example.com/image.jpg"
                    }
                ],
                "created_at": "2025-11-21T01:11:23"
            }
        }


class ChatSessionItem(BaseModel):
    """
    Individual chat session item in the list.
    """
    id: str = Field(..., description="UUID of the chat session")
    title: Optional[str] = Field(None, description="Title of the chat session")
    created_at: datetime = Field(..., description="When the session was created")
    updated_at: Optional[datetime] = Field(None, description="Last update time")
    message_count: int = Field(0, description="Number of messages in this session")
    last_message: Optional[str] = Field(None, description="Preview of the last message")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "title": "Tư vấn về thuốc đau đầu",
                "created_at": "2025-11-21T01:11:23",
                "updated_at": "2025-11-21T01:15:30",
                "message_count": 6,
                "last_message": "Cảm ơn bạn, tôi sẽ thử thuốc này."
            }
        }


class ChatSessionListResponse(BaseModel):
    """
    Response model for listing chat sessions.
    """
    sessions: List[ChatSessionItem] = Field(
        default_factory=list,
        description="List of chat sessions for the user"
    )
    total: int = Field(..., description="Total number of sessions")

    class Config:
        json_schema_extra = {
            "example": {
                "sessions": [
                    {
                        "id": "550e8400-e29b-41d4-a716-446655440000",
                        "title": "Tư vấn về thuốc đau đầu",
                        "created_at": "2025-11-21T01:11:23",
                        "updated_at": "2025-11-21T01:15:30",
                        "message_count": 6,
                        "last_message": "Cảm ơn bạn, tôi sẽ thử thuốc này."
                    }
                ],
                "total": 1
            }
        }

