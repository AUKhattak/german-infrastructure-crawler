"""
Factory pattern for creating crawler instances.
Add a new source type by registering it here.
"""

from typing import Dict, Type
from src.core.base_crawler import BaseCrawler
from src.sources.ckan_source import CKANSource
from src.sources.html_source import HTMLSource
import logging

logger = logging.getLogger(__name__)


class SourceFactory:
    """
    Creates crawler instances based on source type.
    New source types can be registered dynamically.
    """
    
    _registry = {
        'ckan': CKANSource,
        'html': HTMLSource,
        # Add new types here
        # 'socrata': SocrataSource,
        # 'arcgis': ArcGISSource,
    }
    
    @classmethod
    def register(cls, source_type: str, crawler_class: Type[BaseCrawler]):
        """Register a new source type"""
        cls._registry[source_type] = crawler_class
        logger.info(f"Registered source type: {source_type}")
    
    @classmethod
    def create(cls, config: Dict) -> BaseCrawler:
        """Create a crawler instance from configuration"""
        
        source_type = config.get('type', 'html').lower()
        
        if source_type == 'auto':
            source_type = 'html'
        
        if source_type not in cls._registry:
            raise ValueError(f"Unknown source type: {source_type}")
        
        crawler_class = cls._registry[source_type]
        return crawler_class(config)