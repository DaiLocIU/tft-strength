# 0010: Entry Point Needed

## Date

2026-08-26

## Lesson

The user wrote a valid verification function, but running the script produced no output because no entry point called the function.

## Key Insight

A Python file can define functions without executing them. To run a file as a script, add an `if __name__ == "__main__":` block.

## Practice

- Add a script entry point.
- Run from `vision-board-detector`.
- Print matched and missing counts.

## Status

Ready for the user to add the entry point and run the script.

