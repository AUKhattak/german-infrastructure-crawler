from src.models.dataset import Dataset
from src.sources.ckan_source import CKANSource


def test_ckan_transform_extracts_metadata():
	source = CKANSource({"name": "Test", "base_url": "https://example.test", "type": "ckan"})
	dataset = source._transform({
		"id": "1", "title": "Wind energy", "notes": "Assets", "tags": [{"name": "wind"}],
		"organization": {"title": "Public Org"}, "resources": [{"url": "https://example.test/data.csv", "format": "CSV"}],
	})
	assert isinstance(dataset, Dataset)
	assert dataset.organization == "Public Org"
	assert dataset.formats == ["CSV"]
	assert dataset.url == "https://example.test/dataset/1"


def test_ckan_transform_handles_missing_metadata():
	dataset = CKANSource({"name": "Test", "base_url": "https://example.test", "type": "ckan"})._transform({})
	assert dataset.title == "No title"
	assert dataset.url is None


def test_ckan_endpoint_is_joined_safely():
	source = CKANSource({"name": "Test", "base_url": "https://example.test/", "api_path": "/api/search"})
	assert source.search_endpoint == "https://example.test/api/search"


def test_ckan_response_parser_returns_dataset_list(monkeypatch):
	source = CKANSource({"name": "Test", "base_url": "https://example.test", "type": "ckan"})

	class Response:
		status_code = 200
		def json(self):
			return {"success": True, "result": {"results": [{"id": "1", "title": "Power"}]}}

	monkeypatch.setattr(source.http, "get", lambda *args, **kwargs: Response())
	assert len(source.search(type("Context", (), {"query": "power", "limit": 1, "offset": 0})())) == 1
