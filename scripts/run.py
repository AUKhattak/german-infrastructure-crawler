# scripts/run.py
"""
Main entry point.
"""

import sys
import argparse
from pathlib import Path
from typing import Optional, List, Dict

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.registry import SourceRegistry
from src.utils.logger import setup_logging
from src.discovery.catalogue_detector import CatalogueDetector
from src.discovery.seed_loader import load_config, load_seed_sources
from src.processors.deduplicator import deduplicate
from src.utils.http_client import HttpClient
from src.utils.validators import validate_url
import logging
import yaml
from datetime import datetime

logger = logging.getLogger(__name__)
PROJECT_ROOT = Path(__file__).resolve().parent.parent


def main():
    """Main entry point"""
    
    parser = argparse.ArgumentParser(description='Infrastructure Data Crawler')
    parser.add_argument('-q', '--query', nargs='*', 
                       help='Search queries')
    parser.add_argument('-l', '--limit', type=int, default=20,
                       help='Datasets per source')
    parser.add_argument('-c', '--config', default=str(PROJECT_ROOT / 'config' / 'sources.yaml'),
                       help='Configuration file')
    parser.add_argument('-o', '--output', default=str(PROJECT_ROOT / 'output'),
                       help='Output directory')
    parser.add_argument('--max-sources', type=int, default=None,
                       help='Maximum seed sources to process')
    parser.add_argument('--max-datasets', type=int, default=None,
                       help='Maximum datasets to keep per source')
    parser.add_argument('--offline', action='store_true',
                       help='Skip network URL validation')
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging()
    
    print("\n" + "=" * 70)
    print("🏗️ GERMAN INFRASTRUCTURE DATA CRAWLER")
    print("   Enterprise Edition")
    print("=" * 70 + "\n")
    
    # Load config
    config = load_config(args.config)
    queries = args.query or config.get('discovery', {}).get('queries') or config.get('default_queries', ['energy'])
    discovery_config = config.get('discovery', {})
    max_sources = args.max_sources or discovery_config.get('max_sources', 20)
    max_datasets = args.max_datasets or discovery_config.get('max_datasets_per_source', args.limit)

    seeds = load_seed_sources(config)[:max_sources]
    if not args.offline:
        detector = CatalogueDetector()
        detected_seeds = []
        for seed in seeds:
            detected = detector.detect(seed)
            if detected.get('type') != 'unknown':
                detected_seeds.append(detected)
            else:
                logger.warning(f"Skipping unsupported source: {seed.get('name')}")
        config['seed_sources'] = detected_seeds
    else:
        config['seed_sources'] = seeds
    
    # Initialize registry
    registry = SourceRegistry(config)
    
    # Get working sources
    working_sources = registry.get_working_sources()
    print(f"Found {len(working_sources)} working sources")
    
    if not working_sources:
        print("No working sources found. Check your configuration.")
        return
    
    # Run crawls
    all_datasets = []
    stats = {
        'sources_attempted': 0,
        'sources_successful': 0,
        'datasets_found': 0
    }
    
    for source_info in working_sources:
        source_id = source_info['id']
        crawler = registry.sources.get(source_id)
        
        if not crawler:
            continue
        
        stats['sources_attempted'] += 1
        print(f"\n📡 Crawling: {crawler.name}")
        
        try:
            datasets = crawler.batch_search(queries, min(args.limit, max_datasets))[:max_datasets]

            if not args.offline:
                validation_http = HttpClient(
                    rate_limit=crawler.rate_limit,
                    max_retries=crawler.max_retries,
                )
                for dataset in datasets:
                    source_result = validate_url(dataset.url, validation_http)
                    dataset.source_url_status = source_result['status']
                    resource_results = []
                    for resource in dataset.resources:
                        resource_result = validate_url(resource.get('url'), validation_http)
                        resource_results.append(resource_result)
                    dataset.resource_validation = resource_results
                    if dataset.source_url_status == 'accessible':
                        dataset.access_status = 'accessible'
                    elif any(result['status'] == 'accessible' for result in resource_results):
                        dataset.access_status = 'accessible'
                    else:
                        dataset.access_status = 'inaccessible'
            
            if datasets:
                stats['sources_successful'] += 1
                stats['datasets_found'] += len(datasets)
                all_datasets.extend(datasets)
                print(f"   Found {len(datasets)} datasets")
            else:
                print(f"   No datasets found")
                
        except Exception as e:
            print(f"   Error: {e}")
            logger.error(f"Error crawling {crawler.name}: {e}")
    
    unique_datasets = deduplicate(all_datasets)
    
    print(f"\n✅ Total unique datasets: {len(unique_datasets)}")
    
    # Save results
    if unique_datasets:
        output_path = Path(args.output)
        output_path.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # JSON output
        import json
        json_file = output_path / f"infrastructure_data_{timestamp}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump({
                'metadata': {
                    'crawled_at': datetime.now().isoformat(),
                    'total_datasets': len(unique_datasets),
                    'sources_attempted': stats['sources_attempted'],
                    'sources_successful': stats['sources_successful']
                },
                'datasets': [ds.to_dict() for ds in unique_datasets]
            }, f, indent=2, ensure_ascii=False)
        
        # CSV output
        import csv
        csv_file = output_path / f"infrastructure_data_{timestamp}.csv"
        fieldnames = ['dataset_id', 'dataset_title', 'organization', 'source_name', 'data_formats', 
                     'geographic_coverage', 'license', 'last_updated', 
                 'infrastructure_categories', 'source_url', 'download_urls',
                 'access_status', 'source_url_status', 'matched_keywords']
        
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
            writer.writeheader()
            for ds in unique_datasets:
                row = ds.to_dict()
                row['data_formats'] = '; '.join(row.get('data_formats', []))
                row['infrastructure_categories'] = '; '.join(row.get('infrastructure_categories', []))
                row['download_urls'] = '; '.join(row.get('download_urls', []))
                row['matched_keywords'] = '; '.join(row.get('matched_keywords', []))
                writer.writerow(row)
        
        print(f"💾 Results saved to {args.output}/")
        
        # Summary
        print("\n" + "=" * 70)
        print("📊 SUMMARY")
        print("=" * 70)
        
        categories = {}
        for ds in unique_datasets:
            for cat in ds.infrastructure_categories:
                categories[cat] = categories.get(cat, 0) + 1
        
        print("\nInfrastructure Categories:")
        for cat, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
            print(f"   {cat}: {count}")
        
        print("\nSample datasets:")
        for i, ds in enumerate(unique_datasets[:5], 1):
            print(f"   {i}. {ds.title[:60]}")
            print(f"      Source: {ds.source}")
            print(f"      Categories: {', '.join(ds.infrastructure_categories)}")
    
    print("\n" + "=" * 70)
    print("✅ Crawl completed!")


if __name__ == "__main__":
    main()