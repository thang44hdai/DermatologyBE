from fastapi import APIRouter, File, UploadFile, HTTPException
from PIL import Image
import io
import logging

from app.schemas.prediction import PredictionResponse
from app.services.ai_service import ai_service
from app.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/predict", response_model=PredictionResponse, tags=["Prediction"])
async def predict_disease(file: UploadFile = File(...)):
    """
    Predict skin disease from uploaded image
    
    Args:
        file: Image file (supports: jpg, jpeg, png, bmp, gif, tiff, webp)
        
    Returns:
        Prediction result with Vietnamese label
    """
    
    # Get file extension
    file_extension = None
    if file.filename:
        file_extension = '.' + file.filename.lower().split('.')[-1]
    
    # Validate file type
    is_valid = False
    
    # Check by extension
    if file_extension and file_extension in settings.ALLOWED_EXTENSIONS:
        is_valid = True
    
    # Check by content type
    elif file.content_type and file.content_type.startswith('image/'):
        is_valid = True
    
    if not is_valid:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type. Supported formats: {', '.join(settings.ALLOWED_EXTENSIONS)}"
        )
    
    try:
        # Read image
        contents = await file.read()
        
        # Check file size
        if len(contents) > settings.MAX_UPLOAD_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Max size: {settings.MAX_UPLOAD_SIZE / (1024*1024)}MB"
            )
        
        image = Image.open(io.BytesIO(contents))
        
        # Verify it's actually an image
        image.verify()
        
        # Re-open image after verify (verify closes the file)
        image = Image.open(io.BytesIO(contents))
        
        # Predict using AI service
        result = ai_service.predict(image)
        
        logger.info(
            f"File: {file.filename} | Prediction: {result['label_vi']} ({result['confidence']:.2%})"
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing image {file.filename}: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Error processing image: {str(e)}"
        )
