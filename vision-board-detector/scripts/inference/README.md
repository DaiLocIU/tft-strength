# Board State Inference Hosts

The reusable Board State Inference implementation lives in `src/board_detector`.
This directory contains only its command and HTTP hosts:

| Host | Purpose |
| --- | --- |
| `api.py` | Production HTTP endpoint for signed screenshot URLs |
| `board_state_api.py` | Local Board State Intake and correction host |
| `predict_board.py` | Board-detection command launcher |
| `predict_hex_occupancy.py` | Hex-occupancy command launcher |
| `combine_hex_signals.py` | Board State inference command launcher |
| `detect_hexes.py` | Board Geometry visualizer |
| `map_champions_to_hexes.py` | Champion-to-Hex Evidence visualizer |
