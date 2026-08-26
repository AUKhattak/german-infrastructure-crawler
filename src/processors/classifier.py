"""
Infrastructure category classifier.
"""

from typing import Dict, List, Optional, Any
import yaml
from pathlib import Path


class InfrastructureClassifier:
    """
    Classifies datasets into infrastructure categories based on keywords.
    """
    
    def __init__(self, config_path: str = None):
        if config_path is None:
            config_path = str(Path(__file__).resolve().parents[2] / "config" / "categories.yaml")
        self.categories = self._load_categories(config_path)
    
    def _load_categories(self, config_path: str) -> Dict[str, List[str]]:
        """Load category keywords from config"""
        
        config_file = Path(config_path)
        if config_file.exists():
            with open(config_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                return config.get('categories', config)
        
        # Fallback categories
        return {
            'power': ['strom', 'electricity', 'energie', 'kraftwerk', 'netz', 'grid', 'spannung', 'leistung'],
            'renewable': ['wind', 'solar', 'photovoltaik', 'wasser', 'biogas', 'geothermie', 'erneuerbar'],
            'land': ['grundstück', 'fläche', 'kataster', 'parcel', 'land', 'gemeinde', 'stadt', 'bezirk'],
            'telecom': ['telekommunikation', 'internet', 'breitband', '5g', 'fiber', 'kabel', 'netzwerk'],
            'public_facility': ['schule', 'krankenhaus', 'kindergarten', 'feuerwehr', 'polizei', 'rathaus', 'bibliothek']
        }
    
    def classify(self, title: str, description: str, tags: List[str]) -> List[str]:
        """
        Classify a dataset into infrastructure categories.
        """
        
        text = (title + ' ' + description + ' ' + ' '.join(tags)).lower()
        categories = []
        
        for category, keywords in self.categories.items():
            if any(kw in text for kw in keywords):
                categories.append(category)
        
        return categories if categories else ['uncategorized']

    def classify_with_matches(self, title: str, description: str, tags: List[str]):
        """Return deterministic categories and the keywords that matched."""
        text = (title + ' ' + description + ' ' + ' '.join(tags)).lower()
        categories = []
        matched = []
        for category, keywords in self.categories.items():
            category_matches = [keyword for keyword in keywords if keyword.lower() in text]
            if category_matches:
                categories.append(category)
                matched.extend(category_matches)
        return (categories or ['uncategorized'], sorted(set(matched)))