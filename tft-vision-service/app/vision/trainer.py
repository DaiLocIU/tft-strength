import datetime
import glob
import json
import os
from typing import Any, Dict
from PIL import Image

from app.vision.classifier import get_classifier

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MODELS_DIR = os.path.join(PROJECT_ROOT, "data", "models")
os.makedirs(MODELS_DIR, exist_ok=True)


class ContinuousModelTrainer:
    """
    Active Learning Trainer that retrains and updates the CNN embedding index
    from reference icons and confirmed annotations.
    """

    def __init__(self, icons_dir: str = "data/reference_icons"):
        self.icons_dir = icons_dir
        self.manifest_path = os.path.join(MODELS_DIR, "model_manifest.json")

    def get_model_status(self) -> Dict[str, Any]:
        """Returns current model version, architecture, and class counts."""
        classifier = get_classifier(self.icons_dir)
        total_icons = len(glob.glob(os.path.join(self.icons_dir, "*.png")))

        manifest = {}
        if os.path.exists(self.manifest_path):
            with open(self.manifest_path, "r", encoding="utf-8") as f:
                manifest = json.load(f)

        return {
            "status": "ready" if classifier.is_indexed else "untrained",
            "architecture": "MobileNetV2 (Feature Metric Embedding)",
            "version": manifest.get("version", "v1.0.0"),
            "classes_count": len(classifier.classes),
            "classes": classifier.classes,
            "total_templates": total_icons,
            "total_embeddings": len(classifier.embedding_labels) if classifier.embedding_labels else 0,
            "device": str(classifier.device),
            "last_trained_at": manifest.get("last_trained_at", "Just initialized"),
        }

    def train_or_update(self, augment_count: int = 5) -> Dict[str, Any]:
        """
        Retrains / re-indexes the neural network feature embeddings with augmentations.
        """
        classifier = get_classifier(self.icons_dir)
        classifier.reindex(augment_count=augment_count)

        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        version_num = len(glob.glob(os.path.join(self.icons_dir, "*.png")))
        version_str = f"v{version_num}.0-{datetime.datetime.now().strftime('%m%d')}"

        manifest = {
            "version": version_str,
            "architecture": "MobileNetV2 (1280-d Feature Metric Space)",
            "classes_count": len(classifier.classes),
            "classes": classifier.classes,
            "total_embeddings": len(classifier.embedding_labels),
            "last_trained_at": timestamp,
        }

        with open(self.manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)

        return {
            "status": "success",
            "message": f"Successfully updated CNN classifier ({len(classifier.classes)} classes, {len(classifier.embedding_labels)} embeddings)",
            "manifest": manifest,
        }
