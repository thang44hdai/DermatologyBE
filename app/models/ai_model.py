import torch
import torch.nn as nn
import timm


class AttentionFusion(nn.Module):
    """Attention mechanism used to weight fused features"""
    def __init__(self, num_features: int):
        super(AttentionFusion, self).__init__()
        self.attention = nn.Sequential(
            nn.Linear(num_features, num_features // 4),
            nn.ReLU(),
            nn.Linear(num_features // 4, num_features),
            nn.Sigmoid()
        )

    def forward(self, x):
        attention_weights = self.attention(x)
        return x * attention_weights


class SkinDiseaseFusionModel(nn.Module):
    """
    Fusion model combining EfficientNet-B0, EfficientNet-B2, and ResNet50
    for skin disease classification. This version matches the
    optimized training architecture (attention + BatchNorm + larger classifier).
    """

    def __init__(self, num_classes: int):
        super(SkinDiseaseFusionModel, self).__init__()

        # Load pre-trained models
        self.efficientnet_b0 = timm.create_model('efficientnet_b0', pretrained=False)
        self.efficientnet_b2 = timm.create_model('efficientnet_b2', pretrained=False)
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
        self.total_features = self.b0_features + self.b2_features + self.resnet_features

        # Attention and normalization
        self.attention = AttentionFusion(self.total_features)
        self.bn1 = nn.BatchNorm1d(self.total_features)

        # Classification head (matches trained model)
        self.classifier = nn.Sequential(
            nn.Linear(self.total_features, 1024),
            nn.BatchNorm1d(1024),
            nn.ReLU(),
            nn.Dropout(0.5),

            nn.Linear(1024, 512),
            nn.BatchNorm1d(512),
            nn.ReLU(),
            nn.Dropout(0.4),

            nn.Linear(512, 256),
            nn.BatchNorm1d(256),
            nn.ReLU(),
            nn.Dropout(0.3),

            nn.Linear(256, num_classes)
        )

    def forward(self, x):
        # Extract features from each model
        feat_b0 = self.efficientnet_b0(x)
        feat_b2 = self.efficientnet_b2(x)
        feat_resnet = self.resnet50(x)

        # Concatenate features (fusion)
        fused_features = torch.cat([feat_b0, feat_b2, feat_resnet], dim=1)

        # Apply batch normalization then attention
        fused_features = self.bn1(fused_features)
        fused_features = self.attention(fused_features)

        # Classification
        output = self.classifier(fused_features)
        return output
