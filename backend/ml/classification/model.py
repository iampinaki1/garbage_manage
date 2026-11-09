"""
Model A: Waste Image Classifier Architecture.
Implements Transfer Learning using MobileNetV3-Small / EfficientNet-B0
with a customized multi-class classification head for 9 canonical waste categories.
"""

from typing import Tuple, Dict, Any, Optional
from pathlib import Path
import torch
import torch.nn as nn
from torchvision import models

class WasteClassifier(nn.Module):
    """
    Transfer learning classifier for waste segregation.
    Backbone: MobileNetV3-Small (default) or EfficientNet-B0.
    Head: Dropout -> Linear(in_features, 256) -> ReLU -> Dropout -> Linear(256, num_classes)
    """
    def __init__(
        self,
        num_classes: int = 9,
        model_name: str = "mobilenet_v3_small",
        pretrained: bool = True,
        freeze_backbone: bool = False
    ):
        super().__init__()
        self.num_classes = num_classes
        self.model_name = model_name.lower()
        
        if self.model_name == "mobilenet_v3_small":
            weights = models.MobileNet_V3_Small_Weights.DEFAULT if pretrained else None
            backbone = models.mobilenet_v3_small(weights=weights)
            in_features = backbone.classifier[0].in_features
            backbone.classifier = nn.Identity()
            self.backbone = backbone
        elif self.model_name == "efficientnet_b0":
            weights = models.EfficientNet_B0_Weights.DEFAULT if pretrained else None
            backbone = models.efficientnet_b0(weights=weights)
            in_features = backbone.classifier[1].in_features
            backbone.classifier = nn.Identity()
            self.backbone = backbone
        else:
            raise ValueError(f"Unsupported model architecture: {model_name}. Use 'mobilenet_v3_small' or 'efficientnet_b0'.")
            
        if freeze_backbone:
            for param in self.backbone.parameters():
                param.requires_grad = False
                
        # Custom Classification Head (using LayerNorm to support batch_size=1 without train/eval instability)
        self.classifier = nn.Sequential(
            nn.Dropout(p=0.3),
            nn.Linear(in_features, 256),
            nn.LayerNorm(256),
            nn.ReLU(inplace=True),
            nn.Dropout(p=0.2),
            nn.Linear(256, num_classes)
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Computes raw logits for input tensor (B, 3, 224, 224)."""
        features = self.backbone(x)
        logits = self.classifier(features)
        return logits

    @torch.no_grad()
    def predict_proba(self, x: torch.Tensor) -> torch.Tensor:
        """Computes normalized softmax probabilities for input tensor."""
        logits = self.forward(x)
        return torch.softmax(logits, dim=1)

    def save_weights(self, path: Path):
        """Saves model state dictionary and metadata."""
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        torch.save({
            "model_name": self.model_name,
            "num_classes": self.num_classes,
            "state_dict": self.state_dict()
        }, path)

    @classmethod
    def load_from_checkpoint(cls, path: Path, device: torch.device = torch.device("cpu")) -> "WasteClassifier":
        """Factory method restoring model from checkpoint file."""
        checkpoint = torch.load(path, map_location=device, weights_only=False)
        model_name = checkpoint.get("model_name", "mobilenet_v3_small")
        num_classes = checkpoint.get("num_classes", 9)
        
        model = cls(num_classes=num_classes, model_name=model_name, pretrained=False)
        model.load_state_dict(checkpoint["state_dict"])
        model.to(device)
        model.eval()
        return model
