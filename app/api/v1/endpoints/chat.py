from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from sqlalchemy import func
import json
from datetime import datetime

from app.core.dependencies import get_db, get_current_user, get_current_user_ws
from app.schemas.chat import (
    ChatRequest, ChatResponse, ChatSessionListResponse, ChatSessionItem,
    ChatHistoryResponse, ChatMessageItem, ChatWSRequest, ChatWSResponse, ChatWSError
)
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


@router.get("/sessions/{session_id}/messages", response_model=ChatHistoryResponse, status_code=status.HTTP_200_OK)
async def get_chat_history(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    limit: int = 50,
    offset: int = 0
) -> ChatHistoryResponse:
    """
    Get message history for a specific chat session.
    
    Returns all messages in the specified session, ordered chronologically.
    Supports pagination via limit and offset parameters.
    
    Args:
        session_id: UUID of the chat session
        db: Database session dependency
        current_user: Authenticated user from JWT token
        limit: Maximum number of messages to return (default: 50)
        offset: Number of messages to skip (default: 0)
        
    Returns:
        ChatHistoryResponse with list of messages
        
    Raises:
        HTTPException 401: If user is not authenticated
        HTTPException 404: If session not found or doesn't belong to user
        HTTPException 500: If database query fails
    """
    try:
        # Verify session exists and belongs to user
        session = db.query(ChatSessions).filter(
            ChatSessions.id == session_id,
            ChatSessions.user_id == current_user.id,
            ChatSessions.deleted_at.is_(None)
        ).first()
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Chat session '{session_id}' not found or access denied"
            )
        
        # Get total message count
        total_count = db.query(func.count(ChatMessages.id)).filter(
            ChatMessages.session_id == session_id,
            ChatMessages.deleted_at.is_(None)
        ).scalar()
        
        # Get messages with pagination
        messages = db.query(ChatMessages).filter(
            ChatMessages.session_id == session_id,
            ChatMessages.deleted_at.is_(None)
        ).order_by(ChatMessages.created_at.asc()).offset(offset).limit(limit).all()
        
        # Convert to response format
        message_items = []
        for msg in messages:
            # Parse sources from JSON string
            sources = None
            if msg.sources:
                try:
                    sources = json.loads(msg.sources)
                except json.JSONDecodeError:
                    sources = None
            
            message_items.append(ChatMessageItem(
                id=msg.id,
                role=msg.role,
                content=msg.content,
                sources=sources,
                created_at=msg.created_at
            ))
        
        return ChatHistoryResponse(
            session_id=session_id,
            messages=message_items,
            total=total_count or 0
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve chat history: {str(e)}"
        )


@router.websocket("/ws")
async def websocket_chat_endpoint(
    websocket: WebSocket,
    token: str,
    db: Session = Depends(get_db)
):
    """
    WebSocket endpoint for realtime chat with streaming responses.
    
    Connection URL: ws://localhost:8000/api/v1/chat/ws?token=<JWT_TOKEN>
    
    Message format (from client):
    {
        "message": "Your question here",
        "session_id": "optional-session-uuid"
    }
    
    Response format (to client):
    - Status updates: {"type": "status", "status": "message"}
    - Start: {"type": "start", "session_id": "..."}
    - Chunks: {"type": "chunk", "content": "..."}
    - End: {"type": "end", "sources": [...], "created_at": "..."}
    - Error: {"type": "error", "error": "...", "detail": "..."}
    
    Args:
        websocket: WebSocket connection
        token: JWT access token from query parameter
        db: Database session
    """
    await websocket.accept()
    
    try:
        # Authenticate user
        try:
            current_user = await get_current_user_ws(token, db)
            print(f"✅ WebSocket authenticated: user_id={current_user.id}, username={current_user.username}")
        except HTTPException as auth_error:
            error_msg = ChatWSError(
                error="Authentication failed",
                detail=str(auth_error.detail)
            )
            await websocket.send_json(error_msg.model_dump())
            await websocket.close(code=1008)  # Policy violation
            return
        
        # Main message loop
        while True:
            try:
                # Receive message from client
                data = await websocket.receive_json()
                
                # Validate request
                try:
                    request = ChatWSRequest(**data)
                except Exception as validation_error:
                    error_msg = ChatWSError(
                        error="Invalid request format",
                        detail=str(validation_error)
                    )
                    await websocket.send_json(error_msg.model_dump())
                    continue
                
                print(f"📨 WebSocket message from user {current_user.id}: '{request.message[:50]}...'")
                
                # Process chat with streaming
                try:
                    async for event in chat_service.process_chat_streaming(
                        db=db,
                        message=request.message,
                        session_id=request.session_id,
                        user_id=current_user.id
                    ):
                        # Convert event to response schema
                        if event['type'] == 'status':
                            response = ChatWSResponse(
                                type='status',
                                status=event['status']
                            )
                        elif event['type'] == 'start':
                            response = ChatWSResponse(
                                type='start',
                                session_id=event['session_id']
                            )
                        elif event['type'] == 'chunk':
                            response = ChatWSResponse(
                                type='chunk',
                                content=event['content']
                            )
                        elif event['type'] == 'end':
                            response = ChatWSResponse(
                                type='end',
                                sources=event.get('sources'),
                                created_at=event.get('created_at')
                            )
                        else:
                            continue
                        
                        # Send to client
                        await websocket.send_json(response.model_dump(mode='json'))
                    
                    print(f"✅ WebSocket streaming completed for user {current_user.id}")
                    
                except ValueError as ve:
                    # Session not found or access denied
                    error_msg = ChatWSError(
                        error="Invalid session",
                        detail=str(ve)
                    )
                    await websocket.send_json(error_msg.model_dump())
                    
                except RuntimeError as re:
                    # Service error
                    error_msg = ChatWSError(
                        error="Service error",
                        detail=str(re)
                    )
                    await websocket.send_json(error_msg.model_dump())
                    
            except WebSocketDisconnect:
                print(f"🔌 WebSocket disconnected: user_id={current_user.id}")
                break
            except Exception as e:
                print(f"❌ Error in WebSocket message loop: {e}")
                error_msg = ChatWSError(
                    error="Internal error",
                    detail=str(e)
                )
                try:
                    await websocket.send_json(error_msg.model_dump())
                except:
                    pass
                break
                
    except Exception as e:
        print(f"❌ WebSocket connection error: {e}")
        try:
            await websocket.close(code=1011)  # Internal error
        except:
            pass


