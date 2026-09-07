import json
import re
from pathlib import Path
from shutil import copy2
from typing import List, TypedDict, cast

class TaskData(TypedDict):
    image: str


class RectangleValue(TypedDict):
    x: float
    y: float
    width: float
    height: float
    rectanglelabels: List[str]


class YoloRectangle(TypedDict):
    class_id: int
    center_x: float
    center_y: float
    width: float
    height: float


class AnnotationResult(TypedDict):
    type: str
    value: RectangleValue


class AnnotationItem(TypedDict):
    result: List[AnnotationResult]


class TaskItem(TypedDict):
    data: TaskData
    annotations: List[AnnotationItem]

class VerifyResult(TypedDict):
    matched: List[str]
    missing: List[str]
    valid_labels: List[str]
    bad_labels: List[str]



def rectangle_to_yolo(rectangle: RectangleValue, class_id: int) -> YoloRectangle:
    x = rectangle["x"] / 100
    y = rectangle["y"] / 100
    width = rectangle["width"] / 100
    height = rectangle["height"] / 100

    return {
        "class_id": class_id,
        "center_x": x + width / 2,
        "center_y": y + height / 2,
        "width": width,
        "height": height,
    }

def yolo_rectangle_to_line(rectangle: YoloRectangle) -> str:
    return (
        f"{rectangle['class_id']} "
        f"{rectangle['center_x']:.6f} "
        f"{rectangle['center_y']:.6f} "
        f"{rectangle['width']:.6f} "
        f"{rectangle['height']:.6f}"
    )

def write_yolo_label_file(
    image_filename: str,
    yolo_line: str,
    labels_dir: str = 'data/yolo/labels/train',
) -> None:
    labels_path = Path(labels_dir)
    labels_path.mkdir(parents=True, exist_ok=True)
    label_filename = Path(image_filename).with_suffix(".txt").name
    label_path = labels_path / label_filename
    label_path.write_text(yolo_line + "\n", encoding="utf-8")

def copy_yolo_image_file(
    image_filename: str,
    raw_dir: str = 'data/raw',
    images_dir: str = 'data/yolo/images/train',
) -> None:
    raw_path = Path(raw_dir)
    images_path = Path(images_dir)
    images_path.mkdir(parents=True, exist_ok=True)

    source_path = raw_path / image_filename
    destination_path = images_path / image_filename

    copy2(source_path, destination_path)

def verify_labels_match_images(export_path: str, raw_dir: str) -> VerifyResult:
    export_file = Path(export_path)
    raw_path = Path(raw_dir)

    matched = []
    missing = []
    valid_labels = []
    bad_labels = []

    with export_file.open("r", encoding="utf-8") as file:
        tasks = cast(List[TaskItem], json.load(file))

    for task in tasks:
        label_studio_path = task["data"]["image"]
        internal_filename = Path(label_studio_path).name

        original_filename = re.sub(r"^[0-9a-f]{8}-", "", internal_filename)

        image_path = raw_path / original_filename

        if image_path.exists():
            matched.append(original_filename)
        else:
            missing.append(original_filename)

        rectangles = find_board_rectangles(task)
 
        if len(rectangles) == 1:
            valid_labels.append(original_filename)
            yolo_rectangle = rectangle_to_yolo(rectangles[0], 0)
            line = yolo_rectangle_to_line(yolo_rectangle)
            write_yolo_label_file(original_filename, line)
            copy_yolo_image_file(original_filename)
            print(f"line: {line}")
        else:
            bad_labels.append(original_filename)
    
    return {
        "matched": matched,
        "missing": missing,
        "valid_labels": valid_labels,
        "bad_labels": bad_labels,
    }


def find_board_rectangles(task: TaskItem) -> List[RectangleValue]:
    rectangles: List[RectangleValue] = []
    for annotation in task["annotations"]:
        result = annotation["result"]

        for reactangle in result:
            value = reactangle["value"]
            if (reactangle["type"] == 'rectanglelabels' and "board" in value["rectanglelabels"]):
                rectangles.append(value)
    return rectangles


if __name__ == "__main__":
    export_path = "exports/label-studio/board-wrong-map-batch-001.json"
    raw_dir = "data/raw"

    result = verify_labels_match_images(
        export_path, raw_dir)
    matched = result["matched"]
    missing = result["missing"]
    valid_labels = result["valid_labels"]
    bad_labels = result["bad_labels"]

    print(f"matched: {len(matched)}")
    print(f"missing: {len(missing)}")
    print(f"valid_labels: {len(valid_labels)}")
    print(f"bad_labels: {len(bad_labels)}")
    print(f"bad_labels:", bad_labels)
