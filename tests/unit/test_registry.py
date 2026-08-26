from src.core.registry import SourceRegistry


def test_offline_working_sources_skip_live_validation(monkeypatch):
	config = {"seed_sources": [{
		"id": "portal", "name": "Portal", "base_url": "https://example.test", "type": "ckan",
		"active": True,
	}]}
	registry = SourceRegistry(config)
	monkeypatch.setattr(registry, "validate_all", lambda: (_ for _ in ()).throw(
		AssertionError("live validation should not run")
	))

	working = registry.get_working_sources(validate=False)

	assert [source["id"] for source in working] == ["portal"]