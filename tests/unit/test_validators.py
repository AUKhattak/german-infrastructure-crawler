from src.utils.validators import derive_access_status, normalize_url, validate_url


def test_normalize_url_resolves_relative_path():
    assert normalize_url("/data.csv", "https://example.test") == "https://example.test/data.csv"


def test_normalize_url_rejects_non_http():
    assert normalize_url("ftp://example.test/data.csv") is None


def test_validate_url_handles_invalid_input():
    result = validate_url("not-a-url")
    assert result["status"] == "invalid"
    assert result["http_status"] is None


def test_validate_url_records_timestamp_and_normalized_url(monkeypatch):
    class Response:
        status_code = 200
        def close(self):
            pass

    class Client:
        def get(self, url, **kwargs):
            assert url == "https://example.test/data"
            return Response()

    result = validate_url("HTTPS://EXAMPLE.TEST/data", Client())
    assert result["status"] == "accessible"
    assert result["url"] == "https://example.test/data"
    assert result["validated_at"]


def test_access_status_distinguishes_unknown_and_transport_error():
    assert derive_access_status({"status": "not_checked"}, []) == "unknown"
    assert derive_access_status({"status": "error"}, []) == "error"
    assert derive_access_status({"status": "inaccessible"}, []) == "inaccessible"
    assert derive_access_status({"status": "invalid"}, []) == "invalid"


def test_access_status_prefers_any_accessible_resource():
    assert derive_access_status(
        {"status": "error"}, [{"status": "accessible"}]
    ) == "accessible"
