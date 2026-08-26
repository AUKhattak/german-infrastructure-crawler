"""Deterministic dataset deduplication."""

from typing import Iterable, List
from urllib.parse import urlparse, urlunparse

from src.models.dataset import Dataset


def _canonical(value: str) -> str:
    parsed = urlparse(value or "")
    if not parsed.netloc:
        return (value or "").strip().lower()
    return urlunparse((parsed.scheme.lower(), parsed.netloc.lower(), parsed.path.rstrip("/").lower(), "", parsed.query, ""))


def _fingerprints(dataset: Dataset) -> List[str]:
    resource_urls = [_canonical(resource.get("url", "")) for resource in dataset.resources]
    fingerprints = []
    if dataset.id:
        fingerprints.append(f"id:{dataset.id.lower()}")
    if dataset.url:
        fingerprints.append(f"url:{_canonical(dataset.url)}")
    fingerprints.extend(f"download:{url}" for url in resource_urls if url)
    fingerprints.append(f"title:{dataset.title.strip().lower()}|org:{dataset.organization.strip().lower()}")
    return fingerprints


def _completeness(dataset: Dataset) -> int:
    return sum(bool(value) for value in (
        dataset.title, dataset.description, dataset.organization, dataset.url,
        dataset.license, dataset.geographic_coverage,
        dataset.formats, dataset.resources,
    ))


def deduplicate(datasets: Iterable[Dataset]) -> List[Dataset]:
    """Keep the most complete record for each matching fingerprint."""
    selected = []
    fingerprints = {}
    for dataset in datasets:
        matches = [fingerprints[key] for key in _fingerprints(dataset) if key in fingerprints]
        if not matches:
            selected.append(dataset)
            index = len(selected) - 1
            for key in _fingerprints(dataset):
                fingerprints[key] = index
            continue
        best_index = matches[0]
        if _completeness(dataset) > _completeness(selected[best_index]):
            selected[best_index] = dataset
            for key in _fingerprints(dataset):
                fingerprints[key] = best_index
    return selected
