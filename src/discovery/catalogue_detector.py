"""Lightweight public catalogue type detection."""

from typing import Dict

from src.utils.http_client import HttpClient


class CatalogueDetector:
    """Detect supported catalogue types without unrestricted crawling."""

    CKAN_PATHS = (
        "/api/action/package_search",
        "/ckan/api/action/package_search",
        "/api/3/action/package_search",
    )

    def __init__(self, http: HttpClient = None):
        self.http = http or HttpClient()

    def detect(self, source: Dict) -> Dict:
        """Return a copy of a seed with a detected type and status."""
        detected = dict(source)
        configured_type = str(source.get("type", "auto")).lower()
        if configured_type in ("ckan", "html"):
            detected["type"] = configured_type
            detected["detection_status"] = "configured"
            return detected

        base_url = str(source.get("base_url", "")).rstrip("/")
        for api_path in self.CKAN_PATHS:
            try:
                response = self.http.get(
                    base_url + api_path,
                    params={"q": "energy", "rows": 1},
                )
                payload = response.json() if response.status_code == 200 else {}
                if response.status_code == 200 and payload.get("success") is True:
                    detected.update({
                        "type": "ckan",
                        "api_path": api_path,
                        "detection_status": "detected",
                    })
                    return detected
            except Exception:
                continue

        try:
            response = self.http.get(base_url)
            if response.status_code == 200:
                detected.update({"type": "html", "detection_status": "fallback"})
                return detected
        except Exception:
            pass

        detected.update({"type": "unknown", "detection_status": "unsupported"})
        return detected
