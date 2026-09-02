"""Loads synthetic (or, in a real deployment, domain-fed) source records
from data/synthetic/*.json. This is the seam where real Commercial,
Medical, and Clinical source-system connectors would plug in instead —
the rest of the Context Layer only depends on this dict-of-lists shape.
"""

from __future__ import annotations

import json
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "synthetic"

RECORD_TYPES = [
    "institutions",
    "hcps",
    "content",
    "interactions",
    "publications",
    "studies",
    "investigator_sites",
    "msl_interactions",
]


def load_source_data(data_dir: Path = DATA_DIR) -> dict[str, list[dict]]:
    if not data_dir.exists():
        raise FileNotFoundError(
            f"{data_dir} not found. Run `python -m context_layer.data.synthetic_gen` first."
        )
    data = {}
    for name in RECORD_TYPES:
        path = data_dir / f"{name}.json"
        data[name] = json.loads(path.read_text())
    return data
