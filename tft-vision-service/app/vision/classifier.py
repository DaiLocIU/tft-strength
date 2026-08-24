import glob
import os
from typing import Dict, List, Optional, Tuple
import cv2
import numpy as np
import torch
import torch.nn as nn
from torchvision import models, transforms
from PIL import Image

# Use Apple Silicon MPS if available, else CPU
DEVICE = torch.device("mps" if torch.backends.mps.is_available() else "cpu")


class ChampionClassifier:
    """
    Lightweight Deep CNN Champion Classifier using a MobileNetV2 backbone
    with feature metric embeddings and cosine similarity matching.
    """

    def __init__(self, icons_dir: str = "data/reference_icons"):
        self.icons_dir = icons_dir
        self.device = DEVICE
        self.model = self._build_backbone().to(self.device)
        self.model.eval()

        self.transform = transforms.Compose([
            transforms.Resize((128, 128)),
            transforms.ToTensor(),
            transforms.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225],
            ),
        ])

        self.augment_transform = transforms.Compose([
            transforms.Resize((128, 128)),
            transforms.RandomRotation(degrees=15),
            transforms.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2),
            transforms.ToTensor(),
            transforms.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225],
            ),
        ])

        self.embeddings: Optional[torch.Tensor] = None
        self.embedding_labels: List[str] = []
        self.classes: List[str] = []
        self.is_indexed = False

        if os.path.exists(self.icons_dir):
            self.reindex()

    def _build_backbone(self) -> nn.Module:
        """Loads MobileNetV2 with default weights and strips the classifier layer."""
        weights = models.MobileNet_V2_Weights.DEFAULT
        backbone = models.mobilenet_v2(weights=weights)
        # Replace classifier with identity to get 1280-dim feature vector
        backbone.classifier = nn.Identity()
        return backbone

    @torch.no_grad()
    def extract_features(self, pil_image: Image.Image) -> torch.Tensor:
        """Extracts normalized 1280-dim embedding from an image."""
        tensor = self.transform(pil_image).unsqueeze(0).to(self.device)
        features = self.model(tensor)
        # L2 normalize feature embedding
        norm_features = torch.nn.functional.normalize(features, p=2, dim=1)
        return norm_features

    def reindex(self, augment_count: int = 4):
        """
        Indexes all reference icons into a high-dimensional metric vector bank
        with online data augmentation (rotations, color shifts) for robustness.
        """
        embeddings_list = []
        labels_list = []
        unique_classes = set()

        pattern = os.path.join(self.icons_dir, "*.png")
        for filepath in sorted(glob.glob(pattern)):
            filename = os.path.splitext(os.path.basename(filepath))[0].lower()
            # Strip suffixes for canonical name
            for suffix in ["_board", "_shop", "_icon", "_unit", "_left", "_right", "_center", "_bench"]:
                if suffix in filename:
                    filename = filename.replace(suffix, "")
                    break

            unique_classes.add(filename)

            try:
                img = Image.open(filepath).convert("RGB")
            except Exception:
                continue

            # 1. Base embedding
            base_feat = self.extract_features(img)
            embeddings_list.append(base_feat)
            labels_list.append(filename)

            # 2. Augmented embeddings for 3D lighting/angle resilience
            with torch.no_grad():
                for _ in range(augment_count):
                    aug_tensor = self.augment_transform(img).unsqueeze(0).to(self.device)
                    aug_feat = self.model(aug_tensor)
                    aug_feat = torch.nn.functional.normalize(aug_feat, p=2, dim=1)
                    embeddings_list.append(aug_feat)
                    labels_list.append(filename)

        if embeddings_list:
            self.embeddings = torch.cat(embeddings_list, dim=0)  # [N, 1280]
            self.embedding_labels = labels_list
            self.classes = sorted(list(unique_classes))
            self.is_indexed = True
        else:
            self.embeddings = None
            self.embedding_labels = []
            self.classes = []
            self.is_indexed = False

    @torch.no_grad()
    def predict(self, crop_image: Image.Image) -> Tuple[str, float]:
        """
        Predicts champion class and confidence for a cropped region.
        Returns: (champion_name, confidence_0_to_1)
        """
        if not self.is_indexed or self.embeddings is None:
            return ("unknown", 0.0)

        feat = self.extract_features(crop_image)  # [1, 1280]
        # Cosine similarity matrix multiplication
        sims = torch.mm(feat, self.embeddings.t()).squeeze(0)  # [N]

        # Find best matching prototype
        best_val, best_idx = torch.topk(sims, k=1)
        score = float(best_val.item())
        label = self.embedding_labels[best_idx.item()]

        # Map cosine similarity (-1 to 1) into calibrated probability score (0 to 1)
        # Highly correlated features typically score 0.5 to 0.95
        prob = max(0.0, min(1.0, (score - 0.25) / 0.70))
        return (label, round(prob, 3))


# Singleton instance for vision service
classifier_instance: Optional[ChampionClassifier] = None


def get_classifier(icons_dir: str = "data/reference_icons") -> ChampionClassifier:
    global classifier_instance
    if classifier_instance is None:
        classifier_instance = ChampionClassifier(icons_dir=icons_dir)
    return classifier_instance
