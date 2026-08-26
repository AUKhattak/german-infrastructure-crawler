from src.models.dataset import Dataset
from src.processors.deduplicator import deduplicate


def make_dataset(description=""):
    return Dataset("same", "Energy data", description, "Org", "Portal", "ckan")


def test_deduplicates_by_id_and_title():
    assert len(deduplicate([make_dataset(), make_dataset()])) == 1


def test_keeps_most_complete_record():
    result = deduplicate([make_dataset(), make_dataset("Detailed description")])
    assert result[0].description == "Detailed description"
