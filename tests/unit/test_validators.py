from src.utils.validators import normalize_url, validate_url


def test_normalize_url_resolves_relative_path():
    assert normalize_url("/data.csv", "https://example.test") == "https://example.test/data.csv"


def test_normalize_url_rejects_non_http():
    assert normalize_url("ftp://example.test/data.csv") is None


def test_validate_url_handles_invalid_input():
    result = validate_url("not-a-url")
    assert result["status"] == "invalid"
    assert result["http_status"] is None
