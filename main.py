from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
from PIL import Image
import io
import torch
import timm
import pandas as pd
import os
from torchvision import transforms

app = FastAPI()

# Device setup
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Paths
DATASET_FOLDER = "resource"
TRAIN_CSV = os.path.join(DATASET_FOLDER, "train_processed.csv")

# Load label map để lấy num_classes và label_map
df = pd.read_csv(TRAIN_CSV)
label_map = {idx: label for idx, label in enumerate(sorted(df['label'].unique()))}
num_classes = len(label_map)

# Load mô hình
model = timm.create_model("efficientnet_b2", pretrained=False, num_classes=num_classes)
model.load_state_dict(torch.load("skin_disease_model.pth", map_location=device))
model = model.to(device)
model.eval()

# Transformations cho preprocess (giống val_transform)
val_transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.5, 0.5, 0.5], std=[0.5, 0.5, 0.5])
])

# Ánh xạ tên bệnh sang tiếng Việt
disease_mapping = {
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

@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    try:
        # Đọc ảnh từ upload
        contents = await file.read()
        img = Image.open(io.BytesIO(contents)).convert("RGB")

        # Preprocess
        img_tensor = val_transform(img).unsqueeze(0).to(device)

        # Dự đoán
        with torch.no_grad():
            outputs = model(img_tensor)
            probabilities = torch.softmax(outputs, dim=1)
            predicted_idx = torch.argmax(outputs, dim=1).item()
            confidence = probabilities[0][predicted_idx].item()

        # Lấy nhãn tiếng Anh và ánh xạ sang tiếng Việt
        predicted_label_en = label_map[predicted_idx]
        predicted_label_vi = disease_mapping.get(predicted_label_en, predicted_label_en)

        return JSONResponse(content={"label": predicted_label_vi, "confidence": confidence})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)