from src.core.base_crawler import BaseCrawler, CrawlerContext


def __getattr__(name):
    """Load factory and registry lazily to avoid source import cycles."""
    if name == 'SourceFactory':
        from src.core.source_factory import SourceFactory
        return SourceFactory
    if name == 'SourceRegistry':
        from src.core.registry import SourceRegistry
        return SourceRegistry
    raise AttributeError(name)

__all__ = [
    'BaseCrawler',
    'CrawlerContext',
    'SourceFactory',
    'SourceRegistry'
]