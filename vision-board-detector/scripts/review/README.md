# Human Review

This module contains the local tools used to label screenshots and correct
uncertain vision-model evidence.

| Tool | Purpose |
| --- | --- |
| `label_champion_identity.py` | Label champion-identity crops |
| `review_low_confidence_champion_identity.py` | Correct uncertain champion-identity predictions |
| `label_champion_star.py` | Label champion star levels |
| `label_hex_occupancy.py` | Label occupied board hexes |
| `review_hex_occupancy.py` | Inspect labeled hex-occupancy examples |
| `review_combined_champion_names.py` | Review Board State champion-name evidence |

Run a tool by its path from the `vision-board-detector` directory, for example:
`python scripts/review/label_champion_identity.py`.
