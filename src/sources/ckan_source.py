# src/sources/ckan_source.py
"""
CKAN API source implementation.
Handles any CKAN-compatible portal.
"""

from typing import List, Dict, Optional
from src.core.base_crawler import BaseCrawler, CrawlerContext
from src.models.dataset import Dataset
from src.utils.http_client import HttpClient
from src.processors.classifier import InfrastructureClassifier
from src.processors.geocoder import GeographicExtractor
from src.utils.validators import normalize_url
import logging

logger = logging.getLogger(__name__)


class CKANSource(BaseCrawler):
    """
    Crawler for CKAN API sources.
    Works with any CKAN portal by configuration.
    """
    
    def __init__(self, config: Dict):
        super().__init__(config)
        self.http = HttpClient(
            rate_limit=self.rate_limit,
            max_retries=self.max_retries
        )
        self.classifier = InfrastructureClassifier()
        self.geocoder = GeographicExtractor()
        
        # API endpoint - can be overridden in config
        self.api_path = config.get('api_path', '/api/action/package_search')
        self.search_endpoint = f"{self.base_url.rstrip('/')}/{self.api_path.lstrip('/')}"
    
    def validate(self) -> bool:
        """Check if CKAN API is accessible"""
        try:
            response = self.http.get(
                self.search_endpoint,
                params={'q': 'energy', 'rows': 1}
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"CKAN validation failed: {e}")
            return False
    
    def get_capabilities(self) -> Dict:
        return {
            'supports_geolocation': True,
            'supports_license': True,
            'supports_formats': True,
            'supports_tags': True,
            'supports_pagination': True,
            'max_limit': 100,
            'query_format': 'free_text'
        }
    
    def search(self, context: CrawlerContext) -> List[Dataset]:
        """Execute search against CKAN API"""
        
        params = {
            'q': context.query,
            'rows': context.limit,
            'start': context.offset,
            'sort': 'score desc, metadata_modified desc'
        }
        
        try:
            response = self.http.get(self.search_endpoint, params=params)
            
            if response.status_code != 200:
                logger.warning(f"CKAN search failed: {response.status_code}")
                return []
            
            data = response.json()
            if not data.get('success'):
                logger.warning(f"CKAN returned success=False: {data.get('error')}")
                return []
            
            raw_datasets = data.get('result', {}).get('results', [])
            datasets = []
            
            for raw in raw_datasets:
                # Use the factory method
                dataset = self._transform(raw)
                datasets.append(dataset)
            
            logger.info(f"CKAN search returned {len(datasets)} datasets")
            return datasets
            
        except Exception as e:
            logger.error(f"CKAN search error: {e}")
            return []
    
    def _transform(self, raw: Dict) -> Dataset:
        """Transform raw CKAN response to Dataset model"""
        
        # Extract organization
        org = raw.get('organization', {})
        
        # Extract resources
        resources = []
        for r in raw.get('resources', []):
            if r.get('url'):
                resources.append({
                    'name': r.get('name', ''),
                    'format': r.get('format', 'Unknown'),
                    'url': r.get('url', ''),
                    'size': r.get('size'),
                    'description': r.get('description', '')
                })
        
        # Extract tags
        tags = [t.get('name', '') for t in raw.get('tags', [])]
        
        # Build dataset object
        dataset_url = normalize_url(raw.get('url'))
        if not dataset_url and raw.get('id'):
            dataset_url = normalize_url(f"{self.base_url}/dataset/{raw['id']}")
        categories, matched_keywords = self.classifier.classify_with_matches(
            raw.get('title', ''), raw.get('notes', ''), tags
        )

        dataset = Dataset(
            id=raw.get('id', ''),
            title=raw.get('title', 'No title'),
            description=raw.get('notes', '')[:500],
            organization=org.get('title', 'Unknown'),
            organization_id=org.get('id', ''),
            source=self.name,
            source_type='ckan',
            url=dataset_url,
            resources=resources,
            tags=tags,
            license=raw.get('license_title', 'Unknown'),
            created_at=raw.get('metadata_created', ''),
            updated_at=raw.get('metadata_modified', ''),
            is_open=raw.get('isopen', False),
            views=raw.get('num_views', 0),
            downloads=raw.get('num_downloads', 0),
            # Processed fields
            formats=list(set(r['format'] for r in resources if r['format'] != 'Unknown')),
            geographic_coverage=self.geocoder.extract(raw),
            infrastructure_categories=categories,
            matched_keywords=matched_keywords,
            raw_data=raw
        )
        
        return dataset