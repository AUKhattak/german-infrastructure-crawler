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
from src.discovery.candidate_discoverer import CandidateDiscoverer
from src.discovery.seed_loader import load_config, load_settings, load_seed_sources
from src.processors.deduplicator import deduplicate
from src.processors.formatter import write_csv
from src.utils.http_client import HttpClient
from src.utils.validators import derive_access_status, validate_url
import logging
import yaml
from datetime import datetime, timezone

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
    parser.add_argument('--settings', default=str(PROJECT_ROOT / 'config' / 'settings.yaml'),
                       help='Runtime settings file')
    parser.add_argument('-o', '--output', default=str(PROJECT_ROOT / 'output'),
                       help='Output directory')
    parser.add_argument('--max-sources', type=int, default=None,
                       help='Maximum seed sources to process')
    parser.add_argument('--max-datasets', type=int, default=None,
                       help='Maximum datasets to keep per source')
    parser.add_argument('--offline', action='store_true',
                       help='Skip network URL validation')
    
    args = parser.parse_args()
    
    print("\n" + "=" * 70)
    print("🏗️ GERMAN INFRASTRUCTURE DATA CRAWLER")
    print("   Enterprise Edition")
    print("=" * 70 + "\n")
    
    # Load config
    config = load_config(args.config)
    settings = load_settings(args.settings)
    config['runtime_settings'] = settings
    logging_config = settings.get('logging', {})
    setup_logging(
        level=logging_config.get('level', 'INFO'),
        log_file=str(PROJECT_ROOT / logging_config.get('file', 'logs/crawler.log')),
        format_string=logging_config.get('format'),
    )
    queries = args.query or config.get('discovery', {}).get('queries') or config.get('default_queries', ['energy'])
    max_queries = settings.get('crawler', {}).get('max_queries_per_source')
    if max_queries:
        queries = queries[:max_queries]
    discovery_config = config.get('discovery', {})
    max_sources = args.max_sources or discovery_config.get('max_sources', 20)
    crawler_settings = settings.get('crawler', {})
    max_datasets = args.max_datasets or discovery_config.get(
        'max_datasets_per_source', crawler_settings.get('max_datasets_per_source', args.limit)
    )

    seeds = load_seed_sources(config)[:max_sources]
    if not args.offline:
        discovery_settings = settings.get('discovery', {})
        if discovery_settings.get('enabled', False):
            discovery_http = HttpClient(**settings.get('http', {}))
            candidates = CandidateDiscoverer(http=discovery_http).discover(
                seeds,
                max_sources=max_sources,
                max_depth=discovery_settings.get('max_depth', 1),
                max_pages_per_source=discovery_settings.get('max_pages_per_source', 20),
                allowed_domains=discovery_settings.get('allowed_domains', []),
                respect_robots=discovery_settings.get('respect_robots_txt', True),
            )
            seeds = (seeds + candidates)[:max_sources]
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
    working_sources = registry.get_working_sources(validate=not args.offline)
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
                http_settings = settings.get('http', {})
                validation_http = HttpClient(
                    rate_limit=crawler.rate_limit,
                    max_retries=crawler.max_retries,
                    timeout=http_settings.get('timeout', crawler.timeout),
                    backoff_factor=http_settings.get('backoff_factor', crawler.backoff_factor),
                )
                for dataset in datasets:
                    source_result = validate_url(dataset.url, validation_http)
                    dataset.source_url_status = source_result['status']
                    dataset.source_url_validation = source_result
                    resource_results = []
                    for resource in dataset.resources:
                        resource_result = validate_url(resource.get('url'), validation_http)
                        resource_result.update({
                            'name': resource.get('name', ''),
                            'format': resource.get('format', 'Unknown'),
                        })
                        resource_results.append(resource_result)
                    dataset.resource_validation = resource_results
                    dataset.access_status = derive_access_status(source_result, resource_results)
                    dataset.validation_timestamp = datetime.now(timezone.utc).isoformat()
            
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
    
    if settings.get('crawler', {}).get('deduplicate', True):
        unique_datasets = deduplicate(all_datasets)
    else:
        unique_datasets = all_datasets

    validation_settings = settings.get('validation', {})
    filtered_datasets = []
    for dataset in unique_datasets:
        if validation_settings.get('require_url', True) and not dataset.url:
            logger.warning(f"Skipping dataset without source URL: {dataset.title}")
            continue
        if validation_settings.get('require_title', True) and not dataset.title.strip():
            logger.warning("Skipping dataset without title")
            continue
        if len(dataset.description.strip()) < validation_settings.get('min_description_length', 0):
            logger.warning(f"Skipping dataset with short description: {dataset.title}")
            continue
        filtered_datasets.append(dataset)
    unique_datasets = filtered_datasets
    
    print(f"\n✅ Total unique datasets: {len(unique_datasets)}")
    
    # Save results
    if unique_datasets:
        output_path = Path(args.output)
        output_path.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        output_formats = set(settings.get('output', {}).get('formats', ['json', 'csv']))

        # JSON output
        import json
        if 'json' in output_formats:
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
        if 'csv' in output_formats:
            csv_file = output_path / f"infrastructure_data_{timestamp}.csv"
            write_csv(unique_datasets, csv_file)
        
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