from fastapi import APIRouter, File, UploadFile, HTTPException, Depends
from fastapi.responses import JSONResponse
from app.utils.gradcam_utils import draw_boundary, generate_heatmap
from sqlalchemy.orm import Session
from PIL import Image
import io
import logging
import json
from typing import Optional
from datetime import datetime
from tempfile import SpooledTemporaryFile

from app.schemas.prediction import (
    PredictionResponse, 
    ScanHistoryResponse, 
    ScanDetailResponse
)
from app.services.ai_service import ai_service
from app.config import settings
from app.core.dependencies import get_db, get_current_user
from app.models import User, Scans, DiagnosisHistory, Disease, MedicineDiseaseLink, Medicines
from app.utils.file_upload import file_upload_service

router = APIRouter()
logger = logging.getLogger(__name__)


def get_disease_with_medicines(db: Session, disease: Disease) -> dict:
    """Helper function to get disease info with medicines"""
    if not disease:
        return None
    
    # Get medicines for this disease
    medicine_links = db.query(MedicineDiseaseLink).filter(
        MedicineDiseaseLink.disease_id == disease.id
    ).all()
    
    medicines = []
    for link in medicine_links:
        medicine = db.query(Medicines).filter(Medicines.id == link.medicine_id).first()
        if medicine:
            # Parse image_url JSON to list
            images = []
            if medicine.image_url:
                try:
                    images = json.loads(medicine.image_url)
                except:
                    images = [medicine.image_url] if medicine.image_url else []
            
            medicines.append({
                "id": medicine.id,
                "name": medicine.name,
                "description": medicine.description,
                "generic_name": medicine.generic_name,
                "type": medicine.type,
                "dosage": medicine.dosage,
                "side_effects": medicine.side_effects,
                "suitable_for": medicine.suitable_for,
                "price": medicine.price,
                "images": images
            })
    
    return {
        "id": disease.id,
        "disease_name": disease.disease_name,
        "description": disease.description,
        "symptoms": disease.symptoms,
        "treatment": disease.treatment,
        "image_url": disease.image_url,
        "medicines": medicines,
        "created_at": disease.created_at
    }


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
        
        image = Image.open(io.BytesIO(contents)).convert("RGB")
        
        # Verify it's actually an image
        image.verify()
        
        # Re-open image after verify (verify closes the file)
        image = Image.open(io.BytesIO(contents)).convert("RGB")
        
        # 1️⃣ Predict using AI service
        prediction_result = ai_service.predict(image)
        
        # 2️⃣ Generate boundary (highlighted image)
        cam, pred_idx = generate_heatmap(image)
        processed_bytes = draw_boundary(image, cam)
        
        # 3️⃣ Upload Highlighted Image (Lưu ảnh đã khoanh vùng)
        highlighted_file = UploadFile(
            filename=f"highlight_{file.filename}" if file.filename else "highlight.jpg",
            file=io.BytesIO(processed_bytes)
        )
        highlighted_file.file.seek(0)
        
        image_url = await file_upload_service.save_image(
            file=highlighted_file,
            upload_dir="uploads/scans",
            prefix="scan"
        )
        
        # Search disease by Vietnamese label (label_vi)
        disease = db.query(Disease).filter(
            Disease.disease_name == prediction_result['label_vi']
        ).first()
        
        if not disease:
            # Fallback: search by English label if Vietnamese name not found
            disease = db.query(Disease).filter(
                Disease.disease_name == prediction_result['label_en']
            ).first()
        
        if not disease:
            # Create new disease record if not exists
            disease = Disease(
                disease_name=prediction_result['label_vi'],
                description=f"AI-detected: {prediction_result['label_vi']}"
            )
            db.add(disease)
            db.commit()
            db.refresh(disease)
        
        # Create scan record
        scan = Scans(
            user_id=current_user.id,
            image_url=image_url,  # Save URL of highlighted image
            scan_date=datetime.utcnow(),
            status="completed",
            disease_id=disease.id
        )
        db.add(scan)
        db.commit()
        db.refresh(scan)
        
        # Create diagnosis history record
        diagnosis_history = DiagnosisHistory(
            user_id=current_user.id,
            scans_id=scan.id,
            disease_id=disease.id,
            note=f"Confidence: {prediction_result['confidence']:.2%}"
        )
        db.add(diagnosis_history)
        db.commit()
        db.refresh(diagnosis_history)
        
        logger.info(
            f"User {current_user.email} | File: {file.filename} | "
            f"Prediction: {prediction_result['label_vi']} ({prediction_result['confidence']:.2%}) | "
            f"Scan ID: {scan.id}"
        )
        
        # Get disease with medicines
        disease_data = get_disease_with_medicines(db, disease)
        
        # Return response with full disease information
        response_data = {
            "success": True,
            "data": {
                "label_en": prediction_result['label_en'],
                "label_vi": prediction_result['label_vi'],
                "confidence": prediction_result['confidence'],
                "scan_id": scan.id,
                "image_url": image_url,
                "disease": disease_data,
                "diagnosis_history_id": diagnosis_history.id,
                "user_id": current_user.id
            }
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


@router.get("/history", response_model=ScanHistoryResponse)
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
        # Get disease information with medicines
        disease = db.query(Disease).filter(Disease.id == scan.disease_id).first()
        disease_data = get_disease_with_medicines(db, disease) if disease else None
        
        # Get diagnosis history for this scan
        diagnosis_history = db.query(DiagnosisHistory).filter(
            DiagnosisHistory.scans_id == scan.id
        ).first()
        
        result.append({
            "scan_id": scan.id,
            "image_url": scan.image_url,
            "scan_date": scan.scan_date,
            "status": scan.status,
            "disease": disease_data,
            "diagnosis_history": {
                "id": diagnosis_history.id if diagnosis_history else None,
                "note": diagnosis_history.note if diagnosis_history else None,
                "created_at": diagnosis_history.created_at if diagnosis_history else None
            } if diagnosis_history else None
        })
    
    return {
        "total": len(result),
        "skip": skip,
        "limit": limit,
        "scans": result
    }


@router.get("/scan/{scan_id}", response_model=ScanDetailResponse)
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
    
    # Get disease information with medicines
    disease = db.query(Disease).filter(Disease.id == scan.disease_id).first()
    disease_data = get_disease_with_medicines(db, disease) if disease else None
    
    # Get diagnosis history for this scan
    diagnosis_history = db.query(DiagnosisHistory).filter(
        DiagnosisHistory.scans_id == scan.id
    ).first()
    
    return {
        "scan_id": scan.id,
        "user_id": scan.user_id,
        "image_url": scan.image_url,
        "scan_date": scan.scan_date,
        "status": scan.status,
        "disease": disease_data,
        "diagnosis_history": {
            "id": diagnosis_history.id,
            "note": diagnosis_history.note,
            "created_at": diagnosis_history.created_at
        } if diagnosis_history else None
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

@router.post("/detect-boundary", deprecated=True)
async def detect_boundary(file: UploadFile = File(...)):
    """
    ⚠️ DEPRECATED: Use POST /predict instead
    
    This endpoint will be removed in future versions.
    The /predict endpoint now returns the highlighted image automatically.
    """
    # 1️⃣ Load model
    if not ai_service.model_loaded:
        ai_service.load_model()

    # 2️⃣ Read original image
    img_bytes = await file.read()
    image = Image.open(io.BytesIO(img_bytes)).convert("RGB")

    # 3️⃣ Generate cam + boundary
    cam, pred_idx = generate_heatmap(image)
    processed_bytes = draw_boundary(image, cam)

    # 4️⃣ Tạo UploadFile để upload Firebase
    processed_file = UploadFile(
        filename="scan_detected.jpg",
        file=io.BytesIO(processed_bytes)
    )
    

    # Reset pointer (very important)
    processed_file.file.seek(0)

    # 5️⃣ Upload Firebase
    image_url = await file_upload_service.save_image(
        file=processed_file,
        upload_dir="uploads/scans_highlight",
        prefix="scan"
    )

    # 6️⃣ Trả response
    return {
        "success": True,
        "label_en": ai_service.idx_to_label.get(pred_idx),
        "predicted_index": pred_idx,
        "image_url": image_url
    }
