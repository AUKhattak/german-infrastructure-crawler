# src/core/registry.py
"""
Registry for managing all data sources.
Handles discovery, validation, and status tracking.
"""

from typing import Dict, List, Optional
from src.core.source_factory import SourceFactory
from src.core.base_crawler import BaseCrawler
from src.discovery.seed_loader import load_seed_sources
import logging
import time
from datetime import datetime

logger = logging.getLogger(__name__)


class SourceRegistry:
    """
    Manages all sources with health checking and discovery.
    """
    
    def __init__(self, config: Dict):
        self.config = config
        self.sources: Dict[str, BaseCrawler] = {}
        self.source_status: Dict[str, Dict] = {}
        self._initialize()
    
    def _initialize(self):
        """Initialize all sources from configuration"""
        
        sources = load_seed_sources(self.config)
        for source_config in sources:
            source_id = source_config.get('id') or source_config.get('name')
            if not source_config.get('active', True):
                logger.info(f"Skipping inactive source: {source_id}")
                continue
            
            try:
                crawler = SourceFactory.create(source_config)
                self.sources[source_id] = crawler
                self.source_status[source_id] = {
                    'status': 'initialized',
                    'last_check': None,
                    'error': None
                }
                logger.info(f"Initialized source: {source_id}")
            except Exception as e:
                logger.error(f"Failed to initialize {source_id}: {e}")
                self.source_status[source_id] = {
                    'status': 'failed',
                    'last_check': datetime.now().isoformat(),
                    'error': str(e)
                }
    
    def validate_all(self) -> Dict:
        """Validate all sources"""
        
        results = {}
        for source_id, crawler in self.sources.items():
            try:
                is_valid = crawler.validate()
                results[source_id] = is_valid
                self.source_status[source_id].update({
                    'status': 'valid' if is_valid else 'invalid',
                    'last_check': datetime.now().isoformat(),
                    'error': None
                })
                if not is_valid:
                    logger.warning(f"Source validation failed: {source_id}")
            except Exception as e:
                results[source_id] = False
                self.source_status[source_id].update({
                    'status': 'error',
                    'last_check': datetime.now().isoformat(),
                    'error': str(e)
                })
                logger.error(f"Source validation error: {source_id} - {e}")
        
        return results
    
    def get_working_sources(self) -> List[Dict]:
        """Get only working sources"""
        self.validate_all()
        working = []
        
        for source_id, status in self.source_status.items():
            if status.get('status') == 'valid':
                crawler = self.sources.get(source_id)
                if crawler:
                    working.append({
                        'id': source_id,
                        'name': crawler.name,
                        'type': crawler.config.get('type'),
                        'capabilities': crawler.get_capabilities()
                    })
        
        return working
    
    def refresh(self):
        """Refresh source configurations"""
        self._initialize()