from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.dependencies import get_db, get_current_user
from app.schemas.chat import ChatRequest, ChatResponse, ChatSessionListResponse, ChatSessionItem
from app.services.chat_service import chat_service
from app.models.database import ChatSessions, ChatMessages, User


router = APIRouter()


@router.post("/", response_model=ChatResponse, status_code=status.HTTP_200_OK)
async def chat_endpoint(
    request: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> ChatResponse:
    """
    Chat endpoint with RAG (Retrieval-Augmented Generation).
    
    This endpoint allows authenticated users to:
    - Start a new conversation by leaving `session_id` as null
    - Continue an existing conversation by providing a valid `session_id`
    
    Args:
        request: ChatRequest containing message and optional session_id
        db: Database session dependency
        current_user: Authenticated user from JWT token
        
    Returns:
        ChatResponse with session_id, AI response, sources, and timestamp
        
    Raises:
        HTTPException 401: If user is not authenticated
        HTTPException 404: If provided session_id is not found
        HTTPException 500: If chat processing fails
    """
    try:
        # Process the chat message
        result = chat_service.process_chat(
            db=db,
            message=request.message,
            session_id=request.session_id,
            user_id=current_user.id
        )
        
        # Return response following ChatResponse schema
        return ChatResponse(
            session_id=result["session_id"],
            message=result["answer"],
            sources=result["sources"],
            created_at=result["created_at"]
        )
        
    except ValueError as ve:
        # Handle invalid session_id (not found in database)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(ve)
        )
    except RuntimeError as re:
        # Handle service initialization or processing errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chat service error: {str(re)}"
        )
    except Exception as e:
        # Handle unexpected errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )


@router.get("/sessions", response_model=ChatSessionListResponse, status_code=status.HTTP_200_OK)
async def get_user_chat_sessions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> ChatSessionListResponse:
    """
    Get list of chat sessions for the authenticated user.
    
    Returns all chat sessions belonging to the current user, ordered by most recent first.
    Each session includes:
    - Session metadata (id, title, timestamps)
    - Message count
    - Preview of the last message
    
    Args:
        db: Database session dependency
        current_user: Authenticated user from JWT token
        
    Returns:
        ChatSessionListResponse with list of sessions and total count
        
    Raises:
        HTTPException 401: If user is not authenticated
        HTTPException 500: If database query fails
    """
    try:
        # Query user's chat sessions (excluding deleted ones)
        sessions = db.query(ChatSessions).filter(
            ChatSessions.user_id == current_user.id,
            ChatSessions.deleted_at.is_(None)
        ).order_by(ChatSessions.updated_at.desc()).all()
        
        session_items = []
        for session in sessions:
            # Count messages in this session
            message_count = db.query(func.count(ChatMessages.id)).filter(
                ChatMessages.session_id == session.id,
                ChatMessages.deleted_at.is_(None)
            ).scalar()
            
            # Get last message preview
            last_msg = db.query(ChatMessages).filter(
                ChatMessages.session_id == session.id,
                ChatMessages.deleted_at.is_(None)
            ).order_by(ChatMessages.created_at.desc()).first()
            
            last_message_preview = None
            if last_msg:
                # Truncate to 100 characters for preview
                last_message_preview = last_msg.content[:100] + "..." if len(last_msg.content) > 100 else last_msg.content
            
            session_items.append(ChatSessionItem(
                id=session.id,
                title=session.title,
                created_at=session.created_at,
                updated_at=session.updated_at,
                message_count=message_count or 0,
                last_message=last_message_preview
            ))
        
        return ChatSessionListResponse(
            sessions=session_items,
            total=len(session_items)
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve chat sessions: {str(e)}"
        )

