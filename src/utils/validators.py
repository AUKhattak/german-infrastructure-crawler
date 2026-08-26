"""Validation helpers for public catalogue and resource URLs."""

from typing import Dict, Optional
from urllib.parse import urljoin, urlparse, urlunparse

from src.utils.http_client import HttpClient


def normalize_url(url: Optional[str], base_url: Optional[str] = None) -> Optional[str]:
    """Return a canonical HTTP(S) URL or ``None`` for invalid input."""
    if not url or not isinstance(url, str):
        return None
    value = url.strip()
    if base_url:
        value = urljoin(base_url.rstrip("/") + "/", value)
    parsed = urlparse(value)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        return None
    return urlunparse((parsed.scheme.lower(), parsed.netloc.lower(), parsed.path or "/", "", parsed.query, ""))


def validate_url(url: Optional[str], http: HttpClient = None, base_url: Optional[str] = None) -> Dict:
    """Validate one URL using a lightweight streamed GET request."""
    normalized = normalize_url(url, base_url)
    result = {"url": normalized, "status": "invalid", "http_status": None, "error": None}
    if not normalized:
        result["error"] = "URL must use HTTP or HTTPS"
        return result
    client = http or HttpClient()
    try:
        response = client.get(normalized, stream=True)
        result["http_status"] = response.status_code
        result["status"] = "accessible" if response.status_code < 400 else "inaccessible"
        response.close()
    except Exception as exc:
        result.update({"status": "error", "error": str(exc)})
    return result
