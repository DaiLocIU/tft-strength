import glob
import json
import os
import shutil
import uuid
from typing import List, Optional
from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel
from PIL import Image

from app.vision.classifier import get_classifier
from app.vision.matcher import TemplateMatcher
from app.vision.preprocessor import load_image
from app.vision.roi import ROIExtractor
from app.vision.trainer import ContinuousModelTrainer

router = APIRouter(prefix="/api", tags=["icons"])

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
SCREENSHOTS_DIR = os.path.join(DATA_DIR, "screenshots")
ICONS_DIR = os.path.join(DATA_DIR, "reference_icons")
ANNOTATIONS_DIR = os.path.join(DATA_DIR, "annotations")

os.makedirs(SCREENSHOTS_DIR, exist_ok=True)
os.makedirs(ICONS_DIR, exist_ok=True)
os.makedirs(ANNOTATIONS_DIR, exist_ok=True)


class BoxCrop(BaseModel):
    id: Optional[str] = None
    name: str
    ymin: Optional[float] = None
    xmin: Optional[float] = None
    ymax: Optional[float] = None
    xmax: Optional[float] = None
    x: Optional[int] = None
    y: Optional[int] = None
    width: Optional[int] = None
    height: Optional[int] = None
    confidence: Optional[float] = None
    status: Optional[str] = "manual"


class BatchCropRequest(BaseModel):
    screenshot_name: Optional[str] = None
    crops: List[BoxCrop]


class DetectRequest(BaseModel):
    screenshot_name: str
    threshold: Optional[float] = 0.90


class AnnotationItem(BaseModel):
    id: str
    name: str
    x: int
    y: int
    width: int
    height: int
    confidence: Optional[float] = None
    status: str = "confirmed"


class SaveAnnotationRequest(BaseModel):
    screenshot_name: str
    items: List[AnnotationItem]


@router.get("/screenshots")
def list_screenshots():
    """List all available screenshots on the server."""
    files = []
    pattern = os.path.join(SCREENSHOTS_DIR, "*")
    for filepath in sorted(glob.glob(pattern)):
        if filepath.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
            name = os.path.basename(filepath)
            size = os.path.getsize(filepath)
            ann_file = os.path.join(ANNOTATIONS_DIR, f"{os.path.splitext(name)[0]}.json")
            has_annotation = os.path.exists(ann_file)
            files.append({
                "name": name,
                "url": f"/data/screenshots/{name}",
                "size": size,
                "has_annotation": has_annotation,
            })
    return {"screenshots": files}


@router.post("/screenshots/upload")
async def upload_screenshot(file: UploadFile = File(...)):
    """Upload a new screenshot into data/screenshots."""
    filename = file.filename
    clean_name = os.path.basename(filename).replace(" ", "_")
    target_path = os.path.join(SCREENSHOTS_DIR, clean_name)

    with open(target_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    with Image.open(target_path) as img:
        w, h = img.size

    return {
        "status": "success",
        "name": clean_name,
        "url": f"/data/screenshots/{clean_name}",
        "width": w,
        "height": h,
    }


@router.get("/icons")
def list_reference_icons():
    """List all saved reference icons."""
    icons = []
    pattern = os.path.join(ICONS_DIR, "*.png")
    for filepath in sorted(glob.glob(pattern)):
        name = os.path.basename(filepath)
        champ_name = os.path.splitext(name)[0]
        with Image.open(filepath) as img:
            w, h = img.size
        icons.append({
            "filename": name,
            "name": champ_name,
            "url": f"/data/reference_icons/{name}",
            "width": w,
            "height": h,
        })
    return {"icons": icons}


@router.delete("/icons/{filename}")
def delete_reference_icon(filename: str):
    """Delete a reference icon and re-indexes CNN embeddings."""
    target_path = os.path.join(ICONS_DIR, filename)
    if not os.path.exists(target_path):
        raise HTTPException(status_code=404, detail="Icon not found")

    os.remove(target_path)
    # Reindex classifier
    trainer = ContinuousModelTrainer(icons_dir=ICONS_DIR)
    trainer.train_or_update()
    return {"status": "deleted", "filename": filename}


@router.post("/icons/crop-batch")
def crop_batch(req: BatchCropRequest):
    """Crop multiple bounding boxes from a screenshot and save to data/reference_icons/."""
    if not req.screenshot_name:
        raise HTTPException(status_code=400, detail="screenshot_name is required")

    source_path = os.path.join(SCREENSHOTS_DIR, req.screenshot_name)
    if not os.path.exists(source_path):
        raise HTTPException(status_code=404, detail=f"Screenshot '{req.screenshot_name}' not found")

    img = Image.open(source_path)
    w_img, h_img = img.size

    saved_icons = []
    for item in req.crops:
        clean_name = item.name.strip().lower().replace(" ", "_")
        if not clean_name:
            continue

        if item.xmin is not None and item.ymin is not None and item.xmax is not None and item.ymax is not None:
            x1 = max(0, int(item.xmin * w_img))
            y1 = max(0, int(item.ymin * h_img))
            x2 = min(w_img, int(item.xmax * w_img))
            y2 = min(h_img, int(item.ymax * h_img))
        elif item.x is not None and item.y is not None and item.width is not None and item.height is not None:
            x1 = max(0, item.x)
            y1 = max(0, item.y)
            x2 = min(w_img, item.x + item.width)
            y2 = min(h_img, item.y + item.height)
        else:
            continue

        if x2 <= x1 or y2 <= y1:
            continue

        cropped = img.crop((x1, y1, x2, y2))
        filename = f"{clean_name}.png"
        out_path = os.path.join(ICONS_DIR, filename)
        cropped.save(out_path, format="PNG")

        saved_icons.append({
            "name": clean_name,
            "filename": filename,
            "url": f"/data/reference_icons/{filename}",
            "width": x2 - x1,
            "height": y2 - y1,
        })

    # Trigger online model update
    trainer = ContinuousModelTrainer(icons_dir=ICONS_DIR)
    trainer.train_or_update()

    return {
        "status": "success",
        "count": len(saved_icons),
        "saved_icons": saved_icons,
    }


@router.post("/vision/detect")
def detect_screenshot(req: DetectRequest):
    """Runs champion detection over the full board of a screenshot."""
    source_path = os.path.join(SCREENSHOTS_DIR, req.screenshot_name)
    if not os.path.exists(source_path):
        raise HTTPException(status_code=404, detail=f"Screenshot '{req.screenshot_name}' not found")

    matcher = TemplateMatcher(icons_dir=ICONS_DIR)
    if not matcher.templates:
        return {"status": "success", "detections": [], "message": "No templates loaded"}

    full_image = load_image(source_path)
    field_roi, (ox, oy) = ROIExtractor.extract_roi(full_image, "field")

    # Run multi-scale matcher
    detections = matcher.match(
        field_roi,
        threshold=req.threshold if req.threshold is not None else 0.90,
        x_offset=ox,
        y_offset=oy,
    )

    results = []
    for d in detections:
        results.append({
            "id": str(uuid.uuid4()),
            "name": str(d.champion),
            "confidence": float(round(float(d.confidence) * 100, 1)),
            "x": int(d.bbox[0]),
            "y": int(d.bbox[1]),
            "width": int(d.bbox[2]),
            "height": int(d.bbox[3]),
            "status": "detected",
        })

    return {
        "status": "success",
        "count": len(results),
        "detections": results,
    }


@router.post("/annotations/save")
def save_annotation(req: SaveAnnotationRequest):
    """
    Saves verified ground-truth annotations and automatically trains the reference icon
    library with confirmed & corrected crops (Active Learning feedback loop).
    """
    source_path = os.path.join(SCREENSHOTS_DIR, req.screenshot_name)
    if not os.path.exists(source_path):
        raise HTTPException(status_code=404, detail=f"Screenshot '{req.screenshot_name}' not found")

    img = Image.open(source_path)
    base_name = os.path.splitext(req.screenshot_name)[0]
    ann_path = os.path.join(ANNOTATIONS_DIR, f"{base_name}.json")

    # Save JSON dataset annotations
    ann_data = {
        "screenshot": req.screenshot_name,
        "width": img.width,
        "height": img.height,
        "annotations": [item.model_dump() for item in req.items],
    }
    with open(ann_path, "w", encoding="utf-8") as f:
        json.dump(ann_data, f, indent=2)

    # Auto-extract confirmed crops to enhance reference icon templates
    saved_templates = 0
    for item in req.items:
        clean_name = item.name.strip().lower().replace(" ", "_")
        if not clean_name:
            continue
        x1 = max(0, item.x)
        y1 = max(0, item.y)
        x2 = min(img.width, item.x + item.width)
        y2 = min(img.height, item.y + item.height)

        if x2 > x1 and y2 > y1:
            cropped = img.crop((x1, y1, x2, y2))
            out_file = f"{clean_name}.png"
            cropped.save(os.path.join(ICONS_DIR, out_file), format="PNG")
            saved_templates += 1

    # Active learning retraining
    trainer = ContinuousModelTrainer(icons_dir=ICONS_DIR)
    train_res = trainer.train_or_update()

    return {
        "status": "success",
        "saved_annotations_count": len(req.items),
        "saved_templates_count": saved_templates,
        "model_update": train_res,
        "annotation_file": f"/data/annotations/{base_name}.json",
    }


@router.get("/annotations/{screenshot_name}")
def get_annotation(screenshot_name: str):
    """Get existing saved annotations for a screenshot if available."""
    base_name = os.path.splitext(screenshot_name)[0]
    ann_path = os.path.join(ANNOTATIONS_DIR, f"{base_name}.json")
    if not os.path.exists(ann_path):
        return {"has_annotation": False, "annotations": []}

    with open(ann_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    return {"has_annotation": True, "data": data}


@router.get("/model/status")
def get_model_status():
    """Returns current active model status & version."""
    trainer = ContinuousModelTrainer(icons_dir=ICONS_DIR)
    return trainer.get_model_status()


@router.post("/model/retrain")
def retrain_model():
    """Manually triggers online CNN model retraining."""
    trainer = ContinuousModelTrainer(icons_dir=ICONS_DIR)
    return trainer.train_or_update(augment_count=6)
