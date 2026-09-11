"""Make the shared source package available to inference command hosts."""

import sys
from pathlib import Path

scripts_dir = Path(__file__).resolve().parents[1]
if str(scripts_dir) not in sys.path:
    sys.path.insert(0, str(scripts_dir))

source_dir = Path(__file__).resolve().parents[2] / "src"
if str(source_dir) not in sys.path:
    sys.path.insert(0, str(source_dir))
