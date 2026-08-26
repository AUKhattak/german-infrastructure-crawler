"""Discover and validate configured public catalogue seeds."""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.discovery.catalogue_detector import CatalogueDetector
from src.discovery.seed_loader import load_config, load_seed_sources
from src.utils.validators import validate_url


def main():
	parser = argparse.ArgumentParser(description="Discover public catalogue sources")
	parser.add_argument("-c", "--config", default=None)
	parser.add_argument("-o", "--output", default=str(Path(__file__).resolve().parent.parent / "output"))
	args = parser.parse_args()

	config = load_config(args.config)
	limit = config.get("discovery", {}).get("max_sources", 20)
	detector = CatalogueDetector()
	discovered = []
	for seed in load_seed_sources(config)[:limit]:
		detected = detector.detect(seed)
		detected["validation"] = validate_url(detected.get("base_url"))
		discovered.append(detected)

	output_path = Path(args.output)
	output_path.mkdir(parents=True, exist_ok=True)
	with (output_path / "discovered_sources.json").open("w", encoding="utf-8") as handle:
		json.dump({"sources": discovered}, handle, indent=2, ensure_ascii=False)
	print(f"Discovered {len(discovered)} configured catalogue seeds")


if __name__ == "__main__":
	main()
