# src/sources/html_source.py
"""
HTML scraping source implementation.
Handles portals without APIs.
"""

from typing import Optional, List, Dict, Any
from bs4 import BeautifulSoup
from src.core.base_crawler import BaseCrawler, CrawlerContext
from src.models.dataset import Dataset
from src.utils.http_client import HttpClient
from src.utils.robots import RobotsChecker
from src.utils.validators import normalize_url
from src.processors.classifier import InfrastructureClassifier
import logging
import re

logger = logging.getLogger(__name__)


class HTMLSource(BaseCrawler):
    """
    HTML scraper for portals without APIs.
    Configuration-driven with pluggable parsers.
    """
    
    def __init__(self, config: Dict):
        super().__init__(config)
        self.http = HttpClient(
            rate_limit=self.rate_limit,
            max_retries=self.max_retries,
            timeout=self.timeout,
            backoff_factor=self.backoff_factor
        )
        self.robots = RobotsChecker()
        self.classifier = InfrastructureClassifier(self.category_config_path)
        
        # HTML parser configuration
        self.parser_config = config.get('parser', {})
        self.selectors = self.parser_config.get('selectors', {})
        self.dataset_pattern = config.get('dataset_pattern', '/dataset/')
        self.search_path = config.get('search_path', '/suche/')
    
    def validate(self) -> bool:
        """Check if the website is accessible"""
        try:
            response = self.http.get(self.base_url)
            return response.status_code == 200
        except Exception:
            return False
    
    def get_capabilities(self) -> Dict:
        return {
            'supports_geolocation': False,
            'supports_license': True,
            'supports_formats': True,
            'supports_tags': False,
            'supports_pagination': False,
            'max_limit': 50,
            'query_format': 'url_params'
        }
    
    def search(self, context: CrawlerContext) -> List[Dataset]:
        """Scrape search results from HTML"""
        
        search_url = f"{self.base_url}{self.search_path}"
        params = {'q': context.query}

        if not self.robots.allowed(search_url):
            logger.warning(f"Blocked by robots.txt: {search_url}")
            return []
        
        try:
            response = self.http.get(search_url, params=params)
            
            if response.status_code != 200:
                logger.warning(f"HTML search failed: {response.status_code}")
                return []
            
            soup = BeautifulSoup(response.text, 'html.parser')
            datasets = self._parse_search_results(soup, context)
            
            logger.info(f"HTML search found {len(datasets)} datasets")
            return datasets
            
        except Exception as e:
            logger.error(f"HTML search error: {e}")
            return []
    
    def _parse_search_results(self, soup: BeautifulSoup, context: CrawlerContext) -> List[Dataset]:
        """Parse dataset links from search results"""
        
        dataset_links = []
        
        # Try different selector patterns
        selector_patterns = self.selectors.get('dataset_links', [
            f'a[href*="{self.dataset_pattern}"]',
            '.dataset-item a',
            '.result-item a',
            'article a'
        ])
        
        for selector in selector_patterns:
            elements = soup.select(selector)
            if elements:
                logger.info(f"Found {len(elements)} items with selector: {selector}")
                dataset_links.extend(elements)
                break
        
        # Extract and limit
        datasets = []
        for element in dataset_links[:context.limit]:
            dataset = self._extract_from_element(element)
            if dataset:
                datasets.append(dataset)
        
        return datasets
    
    def _extract_from_element(self, element) -> Optional[Dataset]:
        """Extract dataset info from HTML element"""
        
        try:
            # Get title
            title_elem = element.find(['h1', 'h2', 'h3', 'h4', 'h5'])
            title = title_elem.text.strip() if title_elem else 'No title'
            
            # Get URL
            href = element.get('href') if element.name == 'a' else None
            if not href and element.find('a'):
                href = element.find('a').get('href')
            
            if href and not href.startswith('http'):
                href = normalize_url(href, self.base_url)
            
            # Get description and optional licence metadata
            desc_elem = element.select_one(','.join(self.selectors.get(
                'description', ['p', '.description', '.notes']
            )))
            description = desc_elem.text.strip() if desc_elem else ''
            license_elem = element.select_one(','.join(self.selectors.get(
                'license', ['.license', '.licence', '[rel="license"]']
            )))
            if license_elem:
                license_href = license_elem.get('href')
                license_value = (normalize_url(license_href, self.base_url)
                                 if license_href else license_elem.get_text(' ', strip=True))
            else:
                license_value = 'Unknown'
            resources = []
            resource_selectors = self.selectors.get('resources', [])
            resource_elements = element.select(','.join(resource_selectors)) if resource_selectors else []
            for resource_elem in resource_elements:
                resource_url = normalize_url(resource_elem.get('href'), self.base_url)
                if resource_url:
                    resources.append({
                        'name': resource_elem.get_text(' ', strip=True),
                        'format': resource_elem.get('data-format', 'Unknown'),
                        'url': resource_url,
                        'description': '',
                    })
            categories, matched_keywords = self.classifier.classify_with_matches(
                title, description, []
            )
            
            # Create dataset
            return Dataset(
                id=f"{self.name.replace(' ', '_')}_{hash(href)}",
                title=title,
                description=description[:500],
                organization=self.config.get('organization', self.name),
                source=self.name,
                source_type='html',
                url=href,
                resources=resources,
                tags=[],
                license=license_value.strip() if license_value.strip() else 'Unknown',
                created_at='',
                updated_at='',
                is_open=False,
                formats=list(dict.fromkeys([resource['format'] for resource in resources
                                            if resource['format'] != 'Unknown'] or ['HTML'])),
                geographic_coverage='Unknown',
                infrastructure_categories=categories,
                matched_keywords=matched_keywords,
                raw_data={}
            )
            
        except Exception as e:
            logger.debug(f"Error extracting from element: {e}")
            return None