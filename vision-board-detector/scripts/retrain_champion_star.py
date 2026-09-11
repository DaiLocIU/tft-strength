import argparse
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

import _bootstrap  # noqa: F401
from datasets.champion_star.split import split_dataset
from ultralytics import YOLO  # type: ignore[attr-defined]

DEFAULT_LABELED_DIR = Path("data/champion-star/labeled")
DEFAULT_DATASET_DIR = Path("data/champion-star-dataset")
DEFAULT_MODEL_PATH = Path("models/champion-star-classifier.pt")
DEFAULT_PROJECT_DIR = Path("../runs/classify")
DEFAULT_IMAGE_SIZE = 160
DEFAULT_EPOCHS = 100
DEFAULT_BATCH_SIZE = 16
DEFAULT_DEVICE = "mps"


def run_retrain(
    labeled_dir: Path,
    dataset_dir: Path,
    model_path: Path,
    output_model_path: Path,
    project_dir: Path,
    run_name: str,
    image_size: int,
    epochs: int,
    batch_size: int,
    device: str,
    train_ratio: float,
    seed: int,
) -> dict[str, Any]:
    split_dataset(
        labeled_dir,
        dataset_dir,
        train_ratio,
        seed,
        clear_existing=True,
    )

    model = YOLO(model_path)
    model.train(
        data=str(dataset_dir),
        imgsz=image_size,
        epochs=epochs,
        batch=batch_size,
        device=device,
        project=str(project_dir),
        name=run_name,
    )

    best_model_path = project_dir / run_name / "weights" / "best.pt"
    if not best_model_path.exists():
        raise FileNotFoundError(f"Trained best model not found: {best_model_path}")

    output_model_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(best_model_path, output_model_path)

    return {
        "run_dir": str(project_dir / run_name),
        "best_model_path": str(best_model_path),
        "output_model_path": str(output_model_path),
    }


def default_run_name() -> str:
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    return f"champion-star-api-retrain-{timestamp}"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--labeled-dir", type=Path, default=DEFAULT_LABELED_DIR)
    parser.add_argument("--dataset-dir", type=Path, default=DEFAULT_DATASET_DIR)
    parser.add_argument("--model", type=Path, default=DEFAULT_MODEL_PATH)
    parser.add_argument("--output-model", type=Path, default=DEFAULT_MODEL_PATH)
    parser.add_argument("--project", type=Path, default=DEFAULT_PROJECT_DIR)
    parser.add_argument("--name", default=default_run_name())
    parser.add_argument("--imgsz", type=int, default=DEFAULT_IMAGE_SIZE)
    parser.add_argument("--epochs", type=int, default=DEFAULT_EPOCHS)
    parser.add_argument("--batch", type=int, default=DEFAULT_BATCH_SIZE)
    parser.add_argument("--device", default=DEFAULT_DEVICE)
    parser.add_argument("--train-ratio", type=float, default=0.8)
    parser.add_argument("--seed", type=int, default=7)
    args = parser.parse_args()

    result = run_retrain(
        args.labeled_dir,
        args.dataset_dir,
        args.model,
        args.output_model,
        args.project,
        args.name,
        args.imgsz,
        args.epochs,
        args.batch,
        args.device,
        args.train_ratio,
        args.seed,
    )

    print(result)


if __name__ == "__main__":
    main()
