from src.discovery.catalogue_detector import CatalogueDetector


class Response:
    def __init__(self, status_code=200, payload=None):
        self.status_code = status_code
        self._payload = payload or {}

    def json(self):
        return self._payload


def test_detector_identifies_ckan(monkeypatch):
    detector = CatalogueDetector()
    monkeypatch.setattr(detector.http, "get", lambda *args, **kwargs: Response(200, {"success": True}))
    result = detector.detect({"name": "Portal", "base_url": "https://example.test", "type": "auto"})
    assert result["type"] == "ckan"


def test_detector_uses_html_fallback(monkeypatch):
    detector = CatalogueDetector()
    responses = iter([Response(404), Response(404), Response(404), Response(200)])
    monkeypatch.setattr(detector.http, "get", lambda *args, **kwargs: next(responses))
    result = detector.detect({"name": "Portal", "base_url": "https://example.test", "type": "auto"})
    assert result["type"] == "html"
