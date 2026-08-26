# src/models/dataset.py
"""
Data model for datasets with validation.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional
from datetime import datetime
import json


@dataclass
class Dataset:
    """Standard dataset model"""
    
    # Core fields - ALL REQUIRED (NO defaults) - MUST COME FIRST
    id: str
    title: str
    description: str
    organization: str
    source: str                    # ← MOVED UP (was after organization_id)
    source_type: str               # ← MOVED UP (was after organization_id)
    
    # Optional fields - with defaults - MUST COME AFTER required fields
    organization_id: str = ''
    url: str = ''
    license: str = 'Unknown'
    created_at: str = ''
    updated_at: str = ''
    is_open: bool = False
    views: int = 0
    downloads: int = 0
    geographic_coverage: str = 'Unknown'
    access_status: str = 'unknown'
    source_url_status: str = 'not_checked'
    resource_validation: List[Dict] = field(default_factory=list)
    matched_keywords: List[str] = field(default_factory=list)
    
    # List fields - with defaults
    resources: List[Dict] = field(default_factory=list)
    download_urls: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    formats: List[str] = field(default_factory=list)
    infrastructure_categories: List[str] = field(default_factory=list)
    
    # Raw data (for debugging)
    raw_data: Dict = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization"""
        return {
            'dataset_id': self.id,
            'dataset_title': self.title,
            'description': self.description[:500],
            'organization': self.organization,
            'organization_id': self.organization_id,
            'source_name': self.source,
            'source_type': self.source_type,
            'source_url': self.url,
            'download_urls': [r.get('url', '') for r in self.resources if r.get('url')][:5],
            'data_formats': self.formats,
            'geographic_coverage': self.geographic_coverage,
            'license': self.license,
            'last_updated': self.updated_at or self.created_at,
            'access_status': self.access_status,
            'source_url_status': self.source_url_status,
            'resource_validation': self.resource_validation,
            'infrastructure_categories': self.infrastructure_categories,
            'matched_keywords': self.matched_keywords,
            'tags': self.tags[:10],
            'resource_count': len(self.resources),
            'views': self.views,
            'downloads': self.downloads
        }
    
    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Dataset':
        """Create dataset from dictionary"""
        return cls(
            id=data.get('dataset_id', data.get('id', '')),
            title=data.get('dataset_title', data.get('title', 'No title')),
            description=data.get('description', ''),
            organization=data.get('organization', 'Unknown'),
            organization_id=data.get('organization_id', ''),
            source=data.get('source_name', data.get('source', 'Unknown')),
            source_type=data.get('source_type', 'unknown'),
            url=data.get('source_url', data.get('url', '')),
            resources=data.get('resources', []),
            tags=data.get('tags', []),
            license=data.get('license', 'Unknown'),
            created_at=data.get('created_at', ''),
            updated_at=data.get('updated_at', ''),
            is_open=data.get('is_open', False),
            views=data.get('views', 0),
            downloads=data.get('downloads', 0),
            formats=data.get('data_formats', data.get('formats', [])),
            geographic_coverage=data.get('geographic_coverage', 'Unknown'),
            access_status=data.get('access_status', 'unknown'),
            source_url_status=data.get('source_url_status', 'not_checked'),
            resource_validation=data.get('resource_validation', []),
            infrastructure_categories=data.get('infrastructure_categories', []),
            matched_keywords=data.get('matched_keywords', []),
            raw_data=data.get('raw_data', {})
        )