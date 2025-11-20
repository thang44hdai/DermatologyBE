from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_db
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.chat_service import chat_service


router = APIRouter()


@router.post("/", response_model=ChatResponse, status_code=status.HTTP_200_OK)
async def chat_endpoint(
    request: ChatRequest,
    db: Session = Depends(get_db)
) -> ChatResponse:
    """
    Chat endpoint with RAG (Retrieval-Augmented Generation).
    
    This endpoint allows users to:
    - Start a new conversation by leaving `session_id` as null
    - Continue an existing conversation by providing a valid `session_id`
    
    Args:
        request: ChatRequest containing message and optional session_id
        db: Database session dependency
        
    Returns:
        ChatResponse with session_id, AI response, sources, and timestamp
        
    Raises:
        HTTPException 404: If provided session_id is not found
        HTTPException 500: If chat processing fails
    """
    try:
        # Process the chat message
        result = chat_service.process_chat(
            db=db,
            message=request.message,
            session_id=request.session_id
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
