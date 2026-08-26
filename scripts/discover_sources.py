"""Discover and validate configured public catalogue seeds."""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.discovery.catalogue_detector import CatalogueDetector
from src.discovery.candidate_discoverer import CandidateDiscoverer
from src.discovery.seed_loader import load_config, load_settings, load_seed_sources
from src.utils.http_client import HttpClient
from src.utils.validators import validate_url


def main():
	parser = argparse.ArgumentParser(description="Discover public catalogue sources")
	parser.add_argument("-c", "--config", default=None)
	parser.add_argument("-o", "--output", default=str(Path(__file__).resolve().parent.parent / "output"))
	args = parser.parse_args()

	config = load_config(args.config)
	config["runtime_settings"] = load_settings()
	limit = config.get("discovery", {}).get("max_sources", 20)
	detector = CatalogueDetector()
	seeds = load_seed_sources(config)[:limit]
	runtime_settings = config.get("runtime_settings", {})
	discovery = runtime_settings.get("discovery", config.get("discovery", {}))
	if discovery.get("enabled", False):
		candidates = CandidateDiscoverer(http=HttpClient(**runtime_settings.get("http", {}))).discover(
			seeds, max_sources=limit,
			max_depth=discovery.get("max_depth", 1),
			max_pages_per_source=discovery.get("max_pages_per_source", 20),
			allowed_domains=discovery.get("allowed_domains", []),
			respect_robots=discovery.get("respect_robots_txt", True),
		)
		seeds = (seeds + candidates)[:limit]
	discovered = []
	for seed in seeds:
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
