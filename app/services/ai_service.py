import torch
import logging
from typing import Dict, Tuple
from PIL import Image
from fastapi import HTTPException

from app.models.ai_model import SkinDiseaseFusionModel
from app.utils.image_processing import preprocess_image
from app.utils.constants import DISEASE_MAPPING
from app.config import settings

logger = logging.getLogger(__name__)


class AIService:
    """Service for AI model operations"""
    
    def __init__(self):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = None
        self.idx_to_label = {}
        self.model_loaded = False
        
    def load_model(self) -> Tuple[SkinDiseaseFusionModel, Dict]:
        """Load the trained fusion model"""
        try:
            logger.info(f"Loading model from {settings.MODEL_PATH}")

            # Load checkpoint
            checkpoint = torch.load(settings.MODEL_PATH, map_location=self.device)

            # Get metadata (with backward compatibility)
            label_mapping = checkpoint.get('label_mapping', {})
            self.idx_to_label = checkpoint.get('idx_to_label', checkpoint.get('label_to_idx', {}))
            num_classes = checkpoint.get('num_classes', len(self.idx_to_label))

            logger.info(f"Model info: {num_classes} classes")

            # Initialize model (architecture matches trained checkpoint)
            self.model = SkinDiseaseFusionModel(num_classes=num_classes)

            # Load weights (non-strict to allow minor key mismatches across versions)
            load_info = self.model.load_state_dict(checkpoint['model_state_dict'], strict=False)
            if getattr(load_info, 'missing_keys', None) or getattr(load_info, 'unexpected_keys', None):
                logger.warning(
                    f"Model load warnings - missing keys: {load_info.missing_keys}, unexpected keys: {load_info.unexpected_keys}"
                )

            self.model = self.model.to(self.device)
            self.model.eval()

            logger.info(f"Model loaded successfully on {self.device}")
            self.model_loaded = True

            return self.model, self.idx_to_label

        except Exception as e:
            logger.error(f"Error loading model: {e}")
            self.model_loaded = False
            raise

    def predict(self, image: Image.Image) -> Dict:
        """
        Predict disease from image
        
        Args:
            image: PIL Image object
            
        Returns:
            Dictionary with prediction results
        """
        if not self.model_loaded or self.model is None:
            raise HTTPException(status_code=500, detail="Model not loaded")

        try:
            # Preprocess
            image_tensor = preprocess_image(image).to(self.device)

            # Predict
            with torch.no_grad():
                outputs = self.model(image_tensor)
                probabilities = torch.softmax(outputs, dim=1)
                confidence, predicted_idx = torch.max(probabilities, 1)

                predicted_idx = predicted_idx.item()
                confidence = confidence.item()

            # Get label
            label_en = self.idx_to_label.get(
                predicted_idx, 
                self.idx_to_label.get(str(predicted_idx), None)
            )
            
            if label_en is None:
                raise HTTPException(
                    status_code=500, 
                    detail=f"Label not found for index: {predicted_idx}"
                )
                
            label_vi = DISEASE_MAPPING.get(label_en, label_en)

            # Get all predictions sorted by confidence
            all_probs = probabilities[0].cpu().numpy()
            all_predictions = []

            for idx, prob in enumerate(all_probs):
                label = self.idx_to_label.get(idx, self.idx_to_label.get(str(idx), None))
                if label is None:
                    continue
                all_predictions.append({
                    "label_en": label,
                    "label_vi": DISEASE_MAPPING.get(label, label),
                    "confidence": float(prob)
                })

            # Sort by confidence
            all_predictions = sorted(
                all_predictions, 
                key=lambda x: x['confidence'], 
                reverse=True
            )

            return {
                "success": True,
                "label_en": label_en,
                "label_vi": label_vi,
                "confidence": float(confidence),
                "all_predictions": all_predictions[:5]  # Top 5
            }

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Prediction error: {e}")
            raise HTTPException(
                status_code=500, 
                detail=f"Prediction failed: {str(e)}"
            )


# Singleton instance
ai_service = AIService()
