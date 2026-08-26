from src.discovery.seed_loader import load_seed_sources


def test_seed_sources_are_primary_configuration():
    config = {"seed_sources": [{"id": "portal", "name": "Portal", "active": True}]}
    assert load_seed_sources(config)[0]["id"] == "portal"


def test_legacy_sources_remain_supported():
    config = {"sources": {"portal": {"name": "Portal", "active": True}}}
    assert load_seed_sources(config)[0]["id"] == "portal"


def test_inactive_seeds_are_excluded():
    config = {"seed_sources": [{"id": "portal", "active": False}]}
    assert load_seed_sources(config) == []
