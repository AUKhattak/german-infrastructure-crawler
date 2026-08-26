from src.models.dataset import Dataset


def test_serialized_names_are_descriptive():
	dataset = Dataset("id", "Title", "Description", "Org", "Portal", "ckan")
	output = dataset.to_dict()
	assert output["dataset_id"] == "id"
	assert output["dataset_title"] == "Title"
	assert output["source_name"] == "Portal"


def test_new_schema_round_trips():
	dataset = Dataset("id", "Title", "Description", "Org", "Portal", "ckan")
	restored = Dataset.from_dict(dataset.to_dict())
	assert restored.id == dataset.id
	assert restored.title == dataset.title


def test_missing_values_have_explicit_defaults():
	dataset = Dataset("id", "Title", "Description", "Org", "Portal", "ckan")
	assert dataset.source_url_status == "not_checked"
	assert dataset.access_status == "unknown"


def test_resources_and_validation_evidence_round_trip():
	dataset = Dataset(
		"id", "Title", "Description", "Org", "Portal", "ckan",
		resources=[{"name": "Data", "format": "CSV", "url": "https://example.test/data.csv"}],
		source_url_validation={"url": "https://example.test/dataset/id", "status": "accessible"},
		resource_validation=[{"url": "https://example.test/data.csv", "status": "inaccessible"}],
	)
	restored = Dataset.from_dict(dataset.to_dict())
	assert restored.resources == dataset.resources
	assert restored.source_url_validation == dataset.source_url_validation
	assert restored.resource_validation == dataset.resource_validation
