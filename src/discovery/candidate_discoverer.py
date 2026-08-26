"""Controlled discovery of additional public catalogue candidates."""

from collections import deque
from urllib.parse import urlparse

from bs4 import BeautifulSoup

from src.utils.http_client import HttpClient
from src.utils.robots import RobotsChecker
from src.utils.validators import normalize_url


class CandidateDiscoverer:
    """Find likely catalogue hosts from bounded seed-page links."""

    CATALOGUE_TERMS = (
        "dataset", "datasets", "datensatz", "daten", "catalog", "katalog",
        "ckan", "opendata", "open-data", "api",
    )

    def __init__(self, http=None, robots=None):
        self.http = http or HttpClient()
        self.robots = robots or RobotsChecker()

    def discover(self, seeds, max_sources=20, max_depth=1, max_pages_per_source=20,
                 allowed_domains=None, respect_robots=True):
        """Return new candidate source configs within configured bounds."""
        known_origins = {self._origin(seed.get("base_url", "")) for seed in seeds}
        candidates = []
        seen_origins = set(known_origins)
        allowed_domains = set(allowed_domains or [])

        for seed in seeds:
            if len(candidates) + len(seeds) >= max_sources:
                break
            queue = deque([(seed.get("base_url", ""), 0)])
            visited = set()
            pages = 0
            seed_origin = self._origin(seed.get("base_url", ""))

            while queue and pages < max_pages_per_source:
                page_url, depth = queue.popleft()
                normalized_page = normalize_url(page_url)
                if not normalized_page or normalized_page in visited or depth > max_depth:
                    continue
                if respect_robots and not self.robots.allowed(normalized_page):
                    continue
                visited.add(normalized_page)
                pages += 1
                try:
                    response = self.http.get(normalized_page)
                    if response.status_code != 200:
                        continue
                    soup = BeautifulSoup(response.text, "html.parser")
                except Exception:
                    continue

                for link in soup.select("a[href]"):
                    href = normalize_url(link.get("href"), normalized_page)
                    if not href:
                        continue
                    origin = self._origin(href)
                    if not self._allowed(origin, seed_origin, allowed_domains):
                        continue
                    text = f"{link.get_text(' ', strip=True)} {href}".lower()
                    if origin not in seen_origins and any(term in text for term in self.CATALOGUE_TERMS):
                        seen_origins.add(origin)
                        candidates.append({
                            "id": self._candidate_id(origin),
                            "name": urlparse(origin).hostname or origin,
                            "base_url": origin,
                            "type": "auto",
                            "active": True,
                            "discovered_from": seed.get("id") or seed.get("name"),
                            "discovery_depth": depth + 1,
                        })
                        if len(candidates) + len(seeds) >= max_sources:
                            break
                    if depth < max_depth and origin == seed_origin and href not in visited:
                        queue.append((href, depth + 1))
                if len(candidates) + len(seeds) >= max_sources:
                    break

        return candidates

    @staticmethod
    def _origin(url):
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https") or not parsed.netloc:
            return ""
        return f"{parsed.scheme.lower()}://{parsed.netloc.lower()}"

    @staticmethod
    def _candidate_id(origin):
        hostname = urlparse(origin).hostname or "candidate"
        return hostname.replace(".", "_").replace("-", "_")

    @staticmethod
    def _allowed(origin, seed_origin, allowed_domains):
        hostname = urlparse(origin).hostname or ""
        configured = any(hostname == domain or hostname.endswith(f".{domain}")
                         for domain in allowed_domains)
        return origin == seed_origin or configured or not allowed_domains
