# src/processors/geocoder.py
"""
Geographic coverage extractor.
"""

from typing import Dict
import re


class GeographicExtractor:
    """
    Extracts geographic coverage information from dataset metadata.
    """
    
    def __init__(self):
        self.states = [
            'baden-württemberg', 'bayern', 'berlin', 'brandenburg', 'bremen',
            'hamburg', 'hessen', 'mecklenburg-vorpommern', 'niedersachsen',
            'nordrhein-westfalen', 'rheinland-pfalz', 'saarland', 'sachsen',
            'sachsen-anhalt', 'schleswig-holstein', 'thüringen'
        ]
        self.cities = [
            'berlin', 'hamburg', 'münchen', 'köln', 'frankfurt', 'stuttgart',
            'düsseldorf', 'dortmund', 'essen', 'leipzig', 'dresden', 'nürnberg'
        ]
    
    def extract(self, dataset: Dict) -> str:
        """
        Extract geographic coverage from dataset metadata.
        """
        
        # Check spatial field
        spatial = dataset.get('spatial', '')
        if spatial and len(spatial) > 3:
            return spatial[:100]
        
        # Check tags
        for tag in dataset.get('tags', []):
            name = tag.get('name', '').lower()
            if name in ['deutschland', 'germany', 'bundesweit']:
                return 'Germany'
            if name in self.states or name in self.cities:
                return name.title()
        
        # Check text
        text = (dataset.get('title', '') + ' ' + dataset.get('notes', '')).lower()
        
        # Check for Germany
        if 'deutschland' in text or 'germany' in text or 'bundesweit' in text:
            return 'Germany'
        
        # Check for states
        for state in self.states:
            if state in text:
                return state.title()
        
        # Check for cities
        for city in self.cities:
            if city in text:
                return city.title()
        
        return 'Unknown'