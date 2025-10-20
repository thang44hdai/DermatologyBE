from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Dict, List
import torch
import torch.nn as nn
import timm
from torchvision import transforms
from PIL import Image
import io
import uvicorn
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ==========================================
# CONFIGURATION
# ==========================================

MODEL_PATH = "skin_disease_fusion_model_final.pth"
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
IMG_SIZE = 224

# Disease mapping to Vietnamese
DISEASE_MAPPING = {
    "acne": "Mụn trứng cá",
    "acne-vulgaris": "Mụn trứng cá thông thường",
    "actinic-keratosis": "Sừng hóa quang hóa",
    "basal-cell-carcinoma": "Ung thư biểu mô tế bào đáy",
    "basal-cell-carcinoma-morpheiform": "Ung thư biểu mô tế bào đáy dạng morpheiform",
    "dermatofibroma": "U xơ da",
    "dermatomyositis": "Viêm da cơ",
    "dyshidrotic-eczema": "Chàm tổ đỉa",
    "eczema": "Chàm",
    "epidermal-nevus": "Nốt ruồi biểu bì",
    "folliculitis": "Viêm nang lông",
    "kaposi-sarcoma": "Sarcoma Kaposi",
    "keloid": "Sẹo lồi",
    "malignant-melanoma": "U hắc tố ác tính",
    "melanoma": "U hắc tố",
    "mycosis-fungoides": "Nấm da dạng nấm",
    "prurigo-nodularis": "Ngứa cục",
    "pyogenic-granuloma": "U hạt sinh mủ",
    "seborrheic-keratosis": "Sừng hóa tiết bã",
    "squamous-cell-carcinoma": "Ung thư biểu mô tế bào vảy",
    "superficial-spreading-melanoma-ssm": "U hắc tố lan rộng bề mặt",
    "zona": "Zona thần kinh",
    "chickenpox": "Thủy đậu"
}

# ==========================================
# MODEL DEFINITION
# ==========================================


class SkinDiseaseFusionModel(nn.Module):
    """Fusion model combining EfficientNet-B0, EfficientNet-B2, and ResNet50"""

    def __init__(self, num_classes):
        super(SkinDiseaseFusionModel, self).__init__()

        # Load pre-trained models
        self.efficientnet_b0 = timm.create_model(
            'efficientnet_b0', pretrained=False)
        self.efficientnet_b2 = timm.create_model(
            'efficientnet_b2', pretrained=False)
        self.resnet50 = timm.create_model('resnet50', pretrained=False)

        # Get feature dimensions
        self.b0_features = self.efficientnet_b0.num_features
        self.b2_features = self.efficientnet_b2.num_features
        self.resnet_features = self.resnet50.num_features

        # Remove classification heads
        self.efficientnet_b0.classifier = nn.Identity()
        self.efficientnet_b2.classifier = nn.Identity()
        self.resnet50.fc = nn.Identity()

        # Total fused features
        self.total_features = self.b0_features + \
            self.b2_features + self.resnet_features

        # Classification head
        self.classifier = nn.Sequential(
            nn.Linear(self.total_features, 512),
            nn.ReLU(),
            nn.Dropout(0.5),
            nn.Linear(512, 256),
            nn.ReLU(),
            nn.Dropout(0.4),
            nn.Linear(256, num_classes)
        )

    def forward(self, x):
        # Extract features from each model
        feat_b0 = self.efficientnet_b0(x)
        feat_b2 = self.efficientnet_b2(x)
        feat_resnet = self.resnet50(x)

        # Concatenate features (fusion)
        fused_features = torch.cat([feat_b0, feat_b2, feat_resnet], dim=1)

        # Classification
        output = self.classifier(fused_features)
        return output

# ==========================================
# IMAGE PREPROCESSING
# ==========================================


transform = transforms.Compose([
    transforms.Resize((IMG_SIZE, IMG_SIZE)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
])

# ==========================================
# RESPONSE MODELS
# ==========================================


class PredictionItem(BaseModel):
    label_en: str
    label_vi: str
    confidence: float

class PredictionResponse(BaseModel):
    success: bool
    label_en: str
    label_vi: str
    confidence: float
    all_predictions: List[PredictionItem]

class HealthResponse(BaseModel):
    """Response model for health check"""
    status: str
    model_loaded: bool
    device: str

# ==========================================
# LOAD MODEL
# ==========================================


def load_model():
    """Load the trained fusion model"""
    try:
        logger.info(f"Loading model from {MODEL_PATH}")

        # Load checkpoint
        checkpoint = torch.load(MODEL_PATH, map_location=DEVICE)

        # Get metadata
        label_mapping = checkpoint['label_mapping']
        idx_to_label = checkpoint['idx_to_label']
        num_classes = checkpoint['num_classes']

        logger.info(f"Model info: {num_classes} classes")

        # Initialize model
        model = SkinDiseaseFusionModel(num_classes=num_classes)
        model.load_state_dict(checkpoint['model_state_dict'])
        model = model.to(DEVICE)
        model.eval()

        logger.info(f"Model loaded successfully on {DEVICE}")

        return model, idx_to_label

    except Exception as e:
        logger.error(f"Error loading model: {e}")
        raise


# Load model at startup
try:
    model, idx_to_label = load_model()
    MODEL_LOADED = True
except Exception as e:
    logger.error(f"Failed to load model: {e}")
    MODEL_LOADED = False
    model = None
    idx_to_label = {}

# ==========================================
# FASTAPI APP
# ==========================================

app = FastAPI(
    title="Skin Disease Classification API",
    description="API for classifying skin diseases using Fusion Model (EfficientNet-B0 + B2 + ResNet50)",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================================
# HELPER FUNCTIONS
# ==========================================


def preprocess_image(image: Image.Image) -> torch.Tensor:
    """Preprocess image for model input"""
    if image.mode != 'RGB':
        image = image.convert('RGB')

    image_tensor = transform(image)
    image_tensor = image_tensor.unsqueeze(0)  # Add batch dimension
    return image_tensor


def predict_image(image: Image.Image) -> Dict:
    """Predict disease from image"""
    if not MODEL_LOADED or model is None:
        raise HTTPException(status_code=500, detail="Model not loaded")

    try:
        # Preprocess
        image_tensor = preprocess_image(image).to(DEVICE)

        # Predict
        with torch.no_grad():
            outputs = model(image_tensor)
            probabilities = torch.softmax(outputs, dim=1)
            confidence, predicted_idx = torch.max(probabilities, 1)

            predicted_idx = predicted_idx.item()
            confidence = confidence.item()

        # Get label
# ...existing code...
        # Get label
        # Sửa dòng này:
        label_en = idx_to_label.get(
            predicted_idx, idx_to_label.get(str(predicted_idx), None))
        if label_en is None:
            raise HTTPException(
                status_code=500, detail=f"Label not found for index: {predicted_idx}")
        label_vi = DISEASE_MAPPING.get(label_en, label_en)

        # Get all predictions sorted by confidence
        all_probs = probabilities[0].cpu().numpy()
        all_predictions = []

        for idx, prob in enumerate(all_probs):
            label = idx_to_label.get(idx, idx_to_label.get(str(idx), None))
            if label is None:
                continue
            all_predictions.append({
                "label_en": label,
                "label_vi": DISEASE_MAPPING.get(label, label),
                "confidence": float(prob)
            })
# ...existing code...
        # Sort by confidence
        all_predictions = sorted(
            all_predictions, key=lambda x: x['confidence'], reverse=True)

        return {
            "success": True,
            "label_en": label_en,
            "label_vi": label_vi,
            "confidence": float(confidence),
            "all_predictions": all_predictions[:5]  # Top 5
        }

    except Exception as e:
        logger.error(f"Prediction error: {e}")
        raise HTTPException(
            status_code=500, detail=f"Prediction failed: {str(e)}")

# ==========================================
# API ENDPOINTS
# ==========================================


@app.get("/", response_model=HealthResponse)
async def root():
    """Root endpoint - health check"""
    return {
        "status": "running",
        "model_loaded": MODEL_LOADED,
        "device": str(DEVICE)
    }


@app.post("/predict", response_model=PredictionResponse)
async def predict(file: UploadFile = File(...)):
    """
    Predict skin disease from uploaded image

    Args:
        file: Image file (supports: jpg, jpeg, png, bmp, gif, tiff, webp)

    Returns:
        Prediction result with Vietnamese label
    """

    # Supported image extensions
    SUPPORTED_EXTENSIONS = {'.jpg', '.jpeg', '.png',
                            '.bmp', '.gif', '.tiff', '.tif', '.webp', '.jfif'}

    # Get file extension
    file_extension = None
    if file.filename:
        file_extension = '.' + file.filename.lower().split('.')[-1]

    # Validate file type by extension or content type
    is_valid = False

    # Check by extension
    if file_extension and file_extension in SUPPORTED_EXTENSIONS:
        is_valid = True

    # Check by content type
    elif file.content_type and file.content_type.startswith('image/'):
        is_valid = True

    if not is_valid:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type. Supported formats: {', '.join(SUPPORTED_EXTENSIONS)}"
        )

    try:
        # Read image
        contents = await file.read()
        image = Image.open(io.BytesIO(contents))

        # Verify it's actually an image
        image.verify()

        # Re-open image after verify (verify closes the file)
        image = Image.open(io.BytesIO(contents))

        # Predict
        result = predict_image(image)

        logger.info(
            f"File: {file.filename} | Prediction: {result['label_vi']} ({result['confidence']:.2%})")

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing image {file.filename}: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error processing image: {str(e)}")

# ==========================================
# RUN SERVER
# ==========================================

if __name__ == "__main__":
    uvicorn.run(
        "main:app",  # Change "main" to your filename
        host="0.0.0.0",
        port=8000,
        reload=True
    )
