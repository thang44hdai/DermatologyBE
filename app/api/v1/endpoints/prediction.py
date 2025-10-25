from fastapi import APIRouter, File, UploadFile, HTTPException, Depends
from sqlalchemy.orm import Session
from PIL import Image
import io
import logging
import json
from typing import Optional
from datetime import datetime

from app.schemas.prediction import PredictionResponse
from app.services.ai_service import ai_service
from app.config import settings
from app.core.dependencies import get_db, get_current_user
from app.models.database import User, Scans, DiagnosisHistory

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/predict", response_model=PredictionResponse)
async def predict_disease(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Predict skin disease from uploaded image
    
    **Requires Authentication**: Bearer token in Authorization header
    
    Args:
        file: Image file (supports: jpg, jpeg, png, bmp, gif, tiff, webp)
        
    Returns:
        Prediction result with disease information
        
    Process:
        1. Validate image format and size
        2. Run AI model prediction
        3. Find or create diagnosis record
        4. Save scan record to database
        5. Return prediction result with diagnosis info
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
        prediction_result = ai_service.predict(image)
        
        # Get or create diagnosis record
        disease_name = prediction_result['label_en']
        diagnosis = db.query(DiagnosisHistory).filter(DiagnosisHistory.disease_name == disease_name).first()
        
        if not diagnosis:
            # Create new diagnosis record if not exists
            diagnosis = DiagnosisHistory(
                disease_name=disease_name,
                description=f"AI-detected: {prediction_result['label_vi']}",
                severity_level="medium"  # Default severity
            )
            db.add(diagnosis)
            db.commit()
            db.refresh(diagnosis)
        
        # Create scan record
        scan = Scans(
            user_id=current_user.id,
            image_url=file.filename or "uploaded_image.jpg",  # In production, save to storage and store URL
            ai_model_version=getattr(settings, 'AI_MODEL_VERSION', '1.0'),
            diagnosis_id=diagnosis.id,
            confidence=prediction_result['confidence'],
            scan_date=datetime.utcnow()
        )
        db.add(scan)
        db.commit()
        db.refresh(scan)
        
        logger.info(
            f"User {current_user.email} | File: {file.filename} | "
            f"Prediction: {prediction_result['label_vi']} ({prediction_result['confidence']:.2%}) | "
            f"Scan ID: {scan.id}"
        )
        
        # Add scan_id and diagnosis_id to response
        response_data = {
            **prediction_result,
            "scan_id": scan.id,
            "diagnosis_id": diagnosis.id,
            "user_id": current_user.id
        }
        
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing image {file.filename}: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Error processing image: {str(e)}"
        )


@router.get("/history")
async def get_scan_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = 0,
    limit: int = 20
):
    """
    Get scan history for current user
    
    **Requires Authentication**: Bearer token in Authorization header
    
    Args:
        skip: Number of records to skip (for pagination)
        limit: Maximum number of records to return (max 100)
        
    Returns:
        List of scan records with diagnosis information
    """
    if limit > 100:
        limit = 100
    
    scans = db.query(Scans)\
        .filter(Scans.user_id == current_user.id)\
        .order_by(Scans.scan_date.desc())\
        .offset(skip)\
        .limit(limit)\
        .all()
    
    result = []
    for scan in scans:
        diagnosis = db.query(DiagnosisHistory).filter(DiagnosisHistory.id == scan.diagnosis_id).first()
        result.append({
            "scan_id": scan.id,
            "image_url": scan.image_url,
            "confidence": scan.confidence,
            "scan_date": scan.scan_date,
            "diagnosis": {
                "id": diagnosis.id if diagnosis else None,
                "disease_name": diagnosis.disease_name if diagnosis else None,
                "description": diagnosis.description if diagnosis else None,
                "severity_level": diagnosis.severity_level if diagnosis else None
            } if diagnosis else None
        })
    
    return {
        "total": len(result),
        "skip": skip,
        "limit": limit,
        "scans": result
    }


@router.get("/scan/{scan_id}")
async def get_scan_detail(
    scan_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get detailed information about a specific scan
    
    **Requires Authentication**: Bearer token in Authorization header
    
    Args:
        scan_id: ID of the scan record
        
    Returns:
        Detailed scan information with diagnosis
    """
    scan = db.query(Scans).filter(
        Scans.id == scan_id,
        Scans.user_id == current_user.id
    ).first()
    
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    
    diagnosis = db.query(DiagnosisHistory).filter(DiagnosisHistory.id == scan.diagnosis_id).first()
    
    return {
        "scan_id": scan.id,
        "user_id": scan.user_id,
        "image_url": scan.image_url,
        "ai_model_version": scan.ai_model_version,
        "confidence": scan.confidence,
        "scan_date": scan.scan_date,
        "diagnosis": {
            "id": diagnosis.id,
            "disease_name": diagnosis.disease_name,
            "description": diagnosis.description,
            "symptoms": diagnosis.symptoms,
            "treatment": diagnosis.treatment,
            "severity_level": diagnosis.severity_level,
            "created_at": diagnosis.created_at
        } if diagnosis else None
    }


@router.delete("/scan/{scan_id}")
async def delete_scan(
    scan_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a scan record
    
    **Requires Authentication**: Bearer token in Authorization header
    
    Args:
        scan_id: ID of the scan record to delete
        
    Returns:
        Success message
    """
    scan = db.query(Scans).filter(
        Scans.id == scan_id,
        Scans.user_id == current_user.id
    ).first()
    
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    
    db.delete(scan)
    db.commit()
    
    return {"message": "Scan deleted successfully", "scan_id": scan_id}
