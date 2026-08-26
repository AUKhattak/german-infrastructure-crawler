from src.discovery.seed_loader import load_settings, load_seed_sources
from src.sources.ckan_source import CKANSource


def test_seed_sources_are_primary_configuration():
    config = {"seed_sources": [{"id": "portal", "name": "Portal", "active": True}]}
    assert load_seed_sources(config)[0]["id"] == "portal"


def test_legacy_sources_remain_supported():
    config = {"sources": {"portal": {"name": "Portal", "active": True}}}
    assert load_seed_sources(config)[0]["id"] == "portal"


def test_inactive_seeds_are_excluded():
    config = {"seed_sources": [{"id": "portal", "active": False}]}
    assert load_seed_sources(config) == []


def test_runtime_settings_are_loaded():
    settings = load_settings()
    assert settings['http']['timeout'] == 30
    assert settings['crawler']['max_queries_per_source'] == 5


def test_runtime_http_settings_are_applied_to_source():
    source = CKANSource({
        'name': 'Portal',
        'base_url': 'https://example.test',
        'runtime_settings': {'http': {
            'timeout': 12, 'max_retries': 4, 'backoff_factor': 0.5, 'rate_limit': 2,
        }},
    })
    assert source.timeout == 12
    assert source.max_retries == 4
    assert source.backoff_factor == 0.5
    assert source.rate_limit == 2
    assert source.http.timeout == 12
