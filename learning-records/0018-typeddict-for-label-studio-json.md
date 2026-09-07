# 0018: TypedDict For Label Studio JSON

## Date

2026-08-26

## Lesson

The Python equivalent of a TypeScript interface for JSON-shaped dictionaries is `TypedDict`.

## Key Insight

`json.load(file)` returns `Any`, so strict Python needs an explicit type boundary. Use `cast(List[TaskItem], json.load(file))` when the JSON structure has already been validated enough for this learning step.

## Practice

- Define `TaskData`, `RectangleValue`, `AnnotationResult`, `AnnotationItem`, and `TaskItem`.
- Type the loaded tasks as `List[TaskItem]`.
- Understand that `cast` helps the checker but does not validate runtime data.

## Status

Ready for the user to add TypedDict interfaces to `scripts/check_dataset.py`.

