"""Validation helpers for public catalogue and resource URLs."""

from typing import Dict, Optional
from urllib.parse import urljoin, urlparse, urlunparse
from datetime import datetime, timezone

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
    result = {
        "url": normalized, "status": "invalid", "http_status": None, "error": None,
        "validated_at": datetime.now(timezone.utc).isoformat(),
    }
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


def derive_access_status(source_result: Dict, resource_results) -> str:
    """Summarize URL checks without treating transport errors as HTTP failures."""
    results = [source_result] + list(resource_results or [])
    checked = [result for result in results if result.get('status') != 'not_checked']
    if not checked:
        return 'unknown'
    if any(result.get('status') == 'accessible' for result in checked):
        return 'accessible'
    if all(result.get('status') == 'error' for result in checked):
        return 'error'
    if all(result.get('status') == 'invalid' for result in checked):
        return 'invalid'
    return 'inaccessible'
