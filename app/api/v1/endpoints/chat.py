from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from sqlalchemy import func
import json
from datetime import datetime
import logging

from app.core.dependencies import get_db, get_current_user, get_current_user_ws
from app.core.websocket_manager import connection_manager
from app.core.rate_limiter import rate_limiter
from app.schemas.chat import (
    ChatRequest, ChatResponse, ChatSessionListResponse, ChatSessionItem,
    ChatHistoryResponse, ChatMessageItem, ChatWSRequest, ChatWSResponse, ChatWSError
)
from app.services.chat_service import chat_service
from app.models import ChatSessions, ChatMessages, User

logger = logging.getLogger(__name__)


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
    
    Features:
    - JWT authentication
    - Connection management with heartbeat
    - Rate limiting (20 messages/min per user)
    - Automatic reconnection support
    
    Message format (from client):
    {
        "message": "Your question here",
        "session_id": "optional-session-uuid"
    }
    
    Special messages:
    - {"type": "pong"} - Response to ping heartbeat
    
    Response format (to client):
    - Ping: {"type": "ping"}
    - Status updates: {"type": "status", "status": "message"}
    - Start: {"type": "start", "session_id": "..."}
    - Chunks: {"type": "chunk", "content": "..."}
    - End: {"type": "end", "sources": [...], "created_at": "..."}
    - Rate limit: {"type": "rate_limit", "retry_after": seconds}
    - Error: {"type": "error", "error": "...", "detail": "..."}
    
    Args:
        websocket: WebSocket connection
        token: JWT access token from query parameter
        db: Database session
    """
    current_user = None
    
    try:
        # Accept connection first
        await websocket.accept()
        
        # Authenticate user
        try:
            current_user = await get_current_user_ws(token, db)
            logger.info(f"WebSocket authenticated: user_id={current_user.id}, username={current_user.username}")
        except HTTPException as auth_error:
            error_msg = ChatWSError(
                error="Authentication failed",
                detail=str(auth_error.detail)
            )
            await websocket.send_json(error_msg.model_dump())
            await websocket.close(code=1008)  # Policy violation
            return
        
        # Register connection with connection manager
        if not await connection_manager.connect(websocket, current_user.id):
            error_msg = ChatWSError(
                error="Connection limit exceeded",
                detail=f"Maximum {connection_manager.max_connections_per_user} connections per user"
            )
            await websocket.send_json(error_msg.model_dump())
            await websocket.close(code=1008)
            return
        
        logger.info(
            f"WebSocket connected: user_id={current_user.id}, "
            f"connections={connection_manager.get_user_connections(current_user.id)}"
        )
        
        # Main message loop
        while True:
            try:
                # Receive message from client
                data = await websocket.receive_json()
                
                # Update activity timestamp
                connection_manager.update_activity(websocket)
                
                # Handle pong response to ping
                if isinstance(data, dict) and data.get("type") == "pong":
                    logger.debug(f"Received pong from user {current_user.id}")
                    continue
                
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
                
                # Check rate limit
                allowed, retry_after = rate_limiter.check_rate_limit(current_user.id)
                if not allowed:
                    logger.warning(
                        f"Rate limit exceeded for user {current_user.id}, "
                        f"retry after {retry_after:.1f}s"
                    )
                    rate_limit_msg = {
                        "type": "rate_limit",
                        "error": "Rate limit exceeded",
                        "retry_after": retry_after,
                        "detail": f"Please wait {retry_after:.1f} seconds before sending another message"
                    }
                    await websocket.send_json(rate_limit_msg)
                    continue
                
                logger.info(
                    f"WebSocket message from user {current_user.id}: "
                    f"'{request.message[:50]}...'"
                )
                
                # Process chat with streaming
                try:
                    message_start_time = datetime.now()
                    
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
                        
                        # Update activity after each chunk
                        connection_manager.update_activity(websocket)
                    
                    # Log completion time
                    duration = (datetime.now() - message_start_time).total_seconds()
                    logger.info(
                        f"WebSocket streaming completed for user {current_user.id} "
                        f"in {duration:.2f}s"
                    )
                    
                except ValueError as ve:
                    # Session not found or access denied
                    error_msg = ChatWSError(
                        error="Invalid session",
                        detail=str(ve)
                    )
                    await websocket.send_json(error_msg.model_dump())
                    
                except RuntimeError as re:
                    # Service error
                    logger.error(f"Service error for user {current_user.id}: {re}")
                    error_msg = ChatWSError(
                        error="Service error",
                        detail=str(re)
                    )
                    await websocket.send_json(error_msg.model_dump())
                    
            except WebSocketDisconnect:
                logger.info(f"WebSocket disconnected: user_id={current_user.id}")
                break
            except Exception as e:
                logger.error(f"Error in WebSocket message loop for user {current_user.id}: {e}")
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
        logger.error(f"WebSocket connection error: {e}")
        try:
            await websocket.close(code=1011)  # Internal error
        except:
            pass
    finally:
        # Always disconnect from connection manager
        if current_user:
            connection_manager.disconnect(websocket)
            logger.info(
                f"WebSocket cleanup: user_id={current_user.id}, "
                f"remaining_connections={connection_manager.get_user_connections(current_user.id)}"
            )


