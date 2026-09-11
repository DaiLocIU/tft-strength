# Dataset Workflows

Each directory owns the complete data lifecycle for one vision target:
checking or labeling data, collecting examples, splitting the data, and
reviewing it.

| Target | Workflow |
| --- | --- |
| `board` | `check.py` |
| `traits_area` | `check.py`, `split.py` |
| `champion_detector` | `prepare.py` |
| `champion_identity` | `collect_low_confidence.py`, `split.py` |
| `champion_star` | `collect.py`, `split.py` |
| `hex_occupancy` | `inspect.py`, `split.py` |

Run a workflow by its path from the `vision-board-detector` directory, for
example: `python scripts/datasets/traits_area/check.py`.
