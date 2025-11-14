import torch
import cv2
import numpy as np
from PIL import Image
from torchvision import transforms
from typing import Tuple
from app.services.ai_service import ai_service


def generate_heatmap(image: Image.Image) -> Tuple[np.ndarray, int]:
    """
    Generate Grad-CAM heatmap using already-loaded model in ai_service.
    """

    model = ai_service.model
    device = ai_service.device

    if model is None:
        raise Exception("Model is not loaded")

    # Preprocess giống preprocess_image() nhưng không resize crop
    transform = transforms.Compose([
        transforms.Resize((256, 256)),
        transforms.ToTensor(),
        transforms.Normalize(
            [0.485, 0.456, 0.406],
            [0.229, 0.224, 0.225])
    ])

    x = transform(image).unsqueeze(0).to(device)

    # Hooks
    features, grads = [], []

    def fwd_hook(_, __, output):
        features.append(output)

    def bwd_hook(_, grad_in, grad_out):
        grads.append(grad_out[0])

    # Lấy layer cuối cùng của ResNet50
    target_layer = model.resnet50.layer4[-1]
    target_layer.register_forward_hook(fwd_hook)
    target_layer.register_backward_hook(bwd_hook)

    # Forward
    model.eval()
    outputs = model(x)
    pred_idx = outputs.argmax(dim=1).item()

    # Backward
    score = outputs[0, pred_idx]
    model.zero_grad()
    score.backward()

    # Compute Grad-CAM
    fmap = features[0].detach().cpu().numpy()[0]
    grad = grads[0].detach().cpu().numpy()[0]

    weights = np.mean(grad, axis=(1, 2))
    cam = np.maximum(np.sum([w * f for w, f in zip(weights, fmap)], axis=0), 0)

    cam = cv2.resize(cam, image.size)
    cam = cam / (cam.max() + 1e-8)

    return cam, pred_idx


def draw_boundary(image: Image.Image, cam: np.ndarray):
    cam_uint8 = np.uint8(255 * cam)
    cam_blur = cv2.GaussianBlur(cam_uint8, (7, 7), 0)

    _, mask = cv2.threshold(
        cam_blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )

    kernel = np.ones((5, 5), np.uint8)
    mask_dilated = cv2.dilate(mask, kernel, iterations=2)

    contours, _ = cv2.findContours(
        mask_dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )

    img_bgr = np.array(image)[..., ::-1].copy()
    cv2.drawContours(img_bgr, contours, -1, (0, 0, 255), 3)

    _, buffer = cv2.imencode(".jpg", img_bgr)
    return buffer.tobytes()
