"""Minimal robots.txt enforcement for HTML crawling."""

from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser


class RobotsChecker:
    """Cache robots.txt decisions per host and user agent."""

    def __init__(self, user_agent: str = "GermanInfrastructureCrawler/1.0"):
        self.user_agent = user_agent
        self._parsers = {}

    def allowed(self, url: str) -> bool:
        """Return whether the URL is allowed by robots.txt."""
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https") or not parsed.netloc:
            return False
        origin = f"{parsed.scheme}://{parsed.netloc}"
        parser = self._parsers.get(origin)
        if parser is None:
            parser = RobotFileParser(f"{origin}/robots.txt")
            try:
                parser.read()
            except Exception:
                return False
            self._parsers[origin] = parser
        return parser.can_fetch(self.user_agent, url)
