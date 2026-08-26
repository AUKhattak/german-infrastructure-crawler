"""Configuration loading for seed portals."""

from pathlib import Path
from typing import Dict, List

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def load_config(config_path: str = None) -> Dict:
    """Load crawler configuration from YAML."""
    path = Path(config_path) if config_path else PROJECT_ROOT / "config" / "sources.yaml"
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def load_seed_sources(config: Dict) -> List[Dict]:
    """Return seed portals, supporting the legacy ``sources`` mapping."""
    seeds = config.get("seed_sources")
    if seeds is None:
        seeds = []
        for source_id, source in config.get("sources", {}).items():
            item = dict(source)
            item.setdefault("id", source_id)
            seeds.append(item)
    return [dict(seed) for seed in seeds if seed.get("active", True)]
