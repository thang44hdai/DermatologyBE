import torch
from torchvision import transforms
from PIL import Image
from app.config import settings


# Image transformation pipeline
transform = transforms.Compose([
    transforms.Resize((settings.IMG_SIZE, settings.IMG_SIZE)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
])


def preprocess_image(image: Image.Image) -> torch.Tensor:
    """
    Preprocess image for model input
    
    Args:
        image: PIL Image object
        
    Returns:
        Preprocessed image tensor
    """
    if image.mode != 'RGB':
        image = image.convert('RGB')

    image_tensor = transform(image)
    image_tensor = image_tensor.unsqueeze(0)  # Add batch dimension
    return image_tensor
