from pathlib import Path
from typing import TypedDict

from PIL import Image, ImageDraw


class ContactSheetSummary(TypedDict):
    class_name: str
    images: int
    pages: int
    output_files: list[str]


LABELED_DIR = Path("data/hex-occupancy/labeled")
REVIEW_DIR = Path("outputs/review/hex-occupancy")
CLASSES = ["occupied", "empty"]


def collect_image_files(class_name: str) -> list[Path]:
    class_dir = LABELED_DIR / class_name
    return sorted(class_dir.glob("*.png"))


def create_contact_sheet_page(
    image_files: list[Path],
    output_path: Path,
    title: str,
    columns: int = 10,
    thumb_size: int = 96,
) -> None:
    label_height = 24
    title_height = 42
    gap = 8
    rows = (len(image_files) + columns - 1) // columns
    cell_width = thumb_size + gap
    cell_height = thumb_size + label_height + gap
    sheet_width = columns * cell_width + gap
    sheet_height = title_height + rows * cell_height + gap

    sheet = Image.new("RGB", (sheet_width, sheet_height), "white")
    draw = ImageDraw.Draw(sheet)
    draw.text((gap, 12), title, fill="black")

    for index, image_file in enumerate(image_files):
        row = index // columns
        column = index % columns
        x = gap + column * cell_width
        y = title_height + row * cell_height

        image = Image.open(image_file).convert("RGB")
        thumbnail = image.resize((thumb_size, thumb_size))
        sheet.paste(thumbnail, (x, y))
        draw.text((x, y + thumb_size + 4), image_file.stem[-8:], fill="black")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output_path)


def create_class_contact_sheets(
    class_name: str,
    images_per_page: int = 300,
) -> ContactSheetSummary:
    image_files = collect_image_files(class_name)
    output_files: list[str] = []

    if len(image_files) == 0:
        return {
            "class_name": class_name,
            "images": 0,
            "pages": 0,
            "output_files": [],
        }

    page_count = (len(image_files) + images_per_page - 1) // images_per_page

    for page_index in range(page_count):
        start = page_index * images_per_page
        end = start + images_per_page
        page_files = image_files[start:end]
        output_path = REVIEW_DIR / f"{class_name}-page-{page_index + 1:03}.png"
        title = (
            f"{class_name} hex patches "
            f"page {page_index + 1}/{page_count} "
            f"({len(page_files)} images)"
        )
        create_contact_sheet_page(page_files, output_path, title)
        output_files.append(str(output_path))

    return {
        "class_name": class_name,
        "images": len(image_files),
        "pages": page_count,
        "output_files": output_files,
    }


def write_summary(summaries: list[ContactSheetSummary]) -> Path:
    summary_path = REVIEW_DIR / "summary.txt"
    lines: list[str] = ["Hex occupancy review contact sheets", ""]

    for summary in summaries:
        lines.append(
            f"{summary['class_name']}: {summary['images']} images, {summary['pages']} pages"
        )
        for output_file in summary["output_files"]:
            lines.append(f"  {output_file}")
        lines.append("")

    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text("\n".join(lines), encoding="utf-8")
    return summary_path


def main() -> None:
    summaries = [create_class_contact_sheets(class_name) for class_name in CLASSES]
    summary_path = write_summary(summaries)

    for summary in summaries:
        print(
            f"{summary['class_name']}: "
            f"{summary['images']} images, "
            f"{summary['pages']} pages"
        )

    print(f"summary: {summary_path}")


if __name__ == "__main__":
    main()
