"""
Abstract base class for all crawler implementations.
Defines the contract that every source must fulfill.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from dataclasses import dataclass
from src.models.dataset import Dataset


@dataclass
class CrawlerContext:
    """Context passed to crawlers during execution"""
    query: str
    limit: int
    offset: int
    rate_limit: float
    timeout: int


class BaseCrawler(ABC):
    """
    Abstract base crawler.
    All source implementations must inherit from this.
    """
    
    def __init__(self, config: Dict):
        self.config = config
        settings = config.get('runtime_settings', {})
        http_settings = settings.get('http', {})
        category_settings = settings.get('categories', {})
        self.name = config.get('name')
        self.base_url = config.get('base_url')
        self.category_config_path = config.get(
            'category_config_path', category_settings.get('config_path')
        )
        self.rate_limit = config.get('rate_limit', http_settings.get('rate_limit', 1.0))
        self.max_retries = config.get('max_retries', http_settings.get('max_retries', 3))
        self.timeout = config.get('timeout', http_settings.get('timeout', 30))
        self.backoff_factor = config.get('backoff_factor', http_settings.get('backoff_factor', 1))
        self._setup()
    
    def _setup(self):
        """Hook for custom initialization"""
        pass
    
    @abstractmethod
    def search(self, context: CrawlerContext) -> List[Dataset]:
        """
        Search for datasets matching the query.
        Must return a list of Dataset objects.
        """
        pass
    
    @abstractmethod
    def validate(self) -> bool:
        """
        Validate that the source is accessible.
        Returns True if source is working.
        """
        pass
    
    @abstractmethod
    def get_capabilities(self) -> Dict:
        """
        Return what this source can provide.
        e.g., {'supports_geolocation': True, 'supports_license': True}
        """
        pass
    
    def normalize(self, raw_data: Dict) -> Dataset:
        """
        Normalize raw data into standard Dataset model.
        Override in child classes if needed.
        """
        from src.models.dataset import Dataset
        return Dataset.from_dict(raw_data)
    
    def batch_search(self, queries: List[str], limit: int = 20) -> List[Dataset]:
        """
        Search multiple queries.
        Override for optimized batching.
        """
        all_results = []
        for query in queries:
            context = CrawlerContext(
                query=query,
                limit=limit,
                offset=0,
                rate_limit=self.rate_limit,
                timeout=30
            )
            results = self.search(context)
            all_results.extend(results)
        return all_results